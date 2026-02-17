"""
高级 RAG Pipeline

整合混合检索、查询重写、重排序的完整 RAG 管道。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions

from .hybrid_retriever import HybridRetriever
from .query_rewriter import QueryRewriter


@dataclass
class RAGResponse:
    """RAG 系统的响应"""
    answer: str
    sources: List[Dict]
    query: str
    rewritten_query: Optional[str] = None
    retrieval_time: float = 0.0
    generation_time: float = 0.0


class AdvancedRAGPipeline:
    """高级 RAG 管道：混合检索 + 重排序 + 查询重写"""

    def __init__(
        self,
        collection_name: str = "textagent_docs",
        persist_directory: str = "./data/chromadb",
        use_hybrid: bool = True,
        use_rerank: bool = False,
        use_rewrite: bool = True,
        alpha: float = 0.5,
        openai_api_key: Optional[str] = None
    ):
        """
        Args:
            collection_name: ChromaDB 集合名称
            persist_directory: ChromaDB 持久化目录
            use_hybrid: 是否使用混合检索
            use_rerank: 是否使用重排序（需要安装 sentence-transformers）
            use_rewrite: 是否使用查询重写
            alpha: 向量检索权重（0-1）
            openai_api_key: OpenAI API Key
        """
        self.llm_client = OpenAI(api_key=openai_api_key)
        self.use_hybrid = use_hybrid
        self.use_rerank = use_rerank
        self.use_rewrite = use_rewrite

        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=openai_api_key or "",
            model_name="text-embedding-3-small"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )

        # 初始化检索器
        if use_hybrid:
            self.retriever = HybridRetriever(
                chroma_collection=self.collection,
                alpha=alpha
            )
        else:
            self.retriever = None  # 使用纯向量检索

        # 初始化查询重写器
        if use_rewrite:
            self.rewriter = QueryRewriter(self.llm_client)
        else:
            self.rewriter = None

        # 初始化重排序器（可选）
        self.reranker = None
        if use_rerank:
            try:
                from sentence_transformers import CrossEncoder
                self.reranker = CrossEncoderReranker()
            except ImportError:
                print("警告：sentence-transformers 未安装，重排序功能不可用")

    def build_index(self, documents: List[Dict]):
        """构建索引"""
        # 分块
        chunks = self._chunk_documents(documents)

        # 构建向量索引
        self._build_vector_index(chunks)

        # 构建 BM25 索引
        if self.use_hybrid and self.retriever:
            chunk_texts = [c["content"] for c in chunks]
            chunk_ids = [c["id"] for c in chunks]
            self.retriever.build_bm25_index(chunk_texts, chunk_ids)

    def _chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """分块"""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        chinese_separators = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=chinese_separators,
            length_function=len,
        )

        chunks = []
        for doc in documents:
            doc_chunks = text_splitter.split_text(doc["content"])
            for i, chunk_content in enumerate(doc_chunks):
                chunks.append({
                    "id": f"{doc['filename']}_chunk_{i}",
                    "content": chunk_content,
                    "metadata": {
                        **doc.get("metadata", {}),
                        "chunk_index": i,
                        "total_chunks": len(doc_chunks),
                    }
                })
        return chunks

    def _build_vector_index(self, chunks: List[Dict]):
        """构建向量索引"""
        if self.collection.count() > 0:
            print(f"向量索引已存在，包含 {self.collection.count()} 条文档")
            return

        ids = [c["id"] for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]

        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"向量索引构建完成，包含 {len(chunks)} 条文档")

    def query(
        self,
        question: str,
        use_rewrite: bool = True,
        top_k: int = 3
    ) -> RAGResponse:
        """
        执行查询

        Args:
            question: 用户问题
            use_rewrite: 是否使用查询重写
            top_k: 返回的文档数量

        Returns:
            RAGResponse 对象
        """
        import time
        start = time.time()

        # 1. 查询重写（可选）
        query = question
        if self.use_rewrite and use_rewrite and self.rewriter:
            query = self.rewriter.rewrite(question)

        # 2. 检索
        if self.retriever:
            candidates = self.retriever.search(query)
        else:
            # 纯向量检索
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "distances", "metadatas"]
            )
            candidates = [
                {
                    "content": doc,
                    "id": meta.get("doc_id", f"vec_{i}"),
                    "distance": dist,
                    "metadata": meta
                }
                for i, (doc, dist, meta) in enumerate(zip(
                    results["documents"][0],
                    results["distances"][0],
                    results["metadatas"][0]
                ))
            ]

        retrieval_time = time.time() - start

        # 3. 重排序（可选）
        if self.reranker:
            gen_start = time.time()
            reranked = self.reranker.rerank(query, candidates, top_k=top_k)
            final_sources = reranked
            generation_time = time.time() - gen_start + retrieval_time
        else:
            final_sources = candidates[:top_k]
            generation_time = 0  # 将在生成回答后计算

        # 4. 生成回答
        gen_start = time.time()
        answer = self._generate_answer(question, final_sources)
        if not self.reranker:
            generation_time = time.time() - gen_start + retrieval_time
        else:
            generation_time = time.time() - gen_start + (generation_time - retrieval_time)

        return RAGResponse(
            answer=answer,
            sources=final_sources,
            query=question,
            rewritten_query=query if use_rewrite and query != question else None,
            retrieval_time=retrieval_time,
            generation_time=generation_time - retrieval_time
        )

    def _generate_answer(self, question: str, contexts: List[Dict]) -> str:
        """生成回答"""
        context_parts = []
        for i, ctx in enumerate(contexts, 1):
            source = ctx.get("metadata", {}).get("source", "未知")
            context_parts.append(f"【参考资料 {i}】（来源：{source}）\n{ctx['content']}")

        context = "\n\n".join(context_parts)

        prompt = f"""你是公司的内部问答助手，负责回答员工关于公司政策、流程、福利的问题。

根据以下参考资料回答用户的问题。

要求：
1. 只基于参考资料回答，不要编造信息
2. 如果资料中没有相关信息，明确说明"根据现有知识库无法回答"
3. 回答要简洁、专业、友好
4. 如果涉及具体流程，列出关键步骤

参考资料：
{context}

用户问题：{question}

请回答："""

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成回答时出错：{e}"


class CrossEncoderReranker:
    """Cross-Encoder 重排序器（可选功能）"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
        except ImportError:
            raise ImportError(
                "sentence-transformers 未安装。"
                "请运行：pip install sentence-transformers"
            )

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """重排序"""
        pairs = [[query, doc.get("content", "")] for doc in documents]
        scores = self.model.predict(pairs)

        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [
            {**doc, "rerank_score": float(score)}
            for doc, score in scored_docs[:top_k]
        ]
