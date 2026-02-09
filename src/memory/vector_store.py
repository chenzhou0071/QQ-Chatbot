"""向量数据库管理（使用阿里云Embedding）"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from pathlib import Path
import hashlib
import requests

from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("vector_store")

class VectorStore:
    """Chroma向量数据库管理器（阿里云Embedding）"""
    
    def __init__(self, persist_dir: str = "data/chroma"):
        """初始化向量数据库"""
        self.config = get_config()
        
        # 阿里云API配置
        self.api_key = self.config.dashscope_api_key
        self.embedding_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        
        # 创建持久化目录
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 创建集合
        self.collection = self.client.get_or_create_collection(
            name="chat_memory",
            metadata={"description": "聊天记忆向量库"}
        )
        
        logger.info(f"向量数据库初始化完成，当前记录数: {self.collection.count()}")
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """调用阿里云API获取文本向量"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text-embedding-v1",
                "input": {
                    "texts": [text]
                }
            }
            
            response = requests.post(
                self.embedding_url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result['output']['embeddings'][0]['embedding']
                return embedding
            else:
                logger.error(f"获取向量失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"调用阿里云Embedding API失败: {e}")
            return None
    
    def add_memory(self, 
                   chat_id: str,
                   content: str, 
                   sender_id: str,
                   sender_name: str,
                   chat_type: str,
                   timestamp: str):
        """添加聊天记忆"""
        try:
            # 获取向量
            embedding = self._get_embedding(content)
            if not embedding:
                logger.warning(f"跳过记忆（向量生成失败）: {content[:30]}...")
                return
            
            # 存储到向量库
            self.collection.add(
                ids=[chat_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "chat_type": chat_type,
                    "timestamp": timestamp
                }]
            )
            
            logger.debug(f"添加记忆: {content[:30]}...")
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
    
    def search_memory(self, 
                      query: str, 
                      n_results: int = 5,
                      chat_type: Optional[str] = None) -> List[Dict]:
        """搜索相关记忆"""
        try:
            # 获取查询向量
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                logger.warning("搜索失败：无法生成查询向量")
                return []
            
            # 构建过滤条件
            where = {"chat_type": chat_type} if chat_type else None
            
            # 搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            # 格式化结果
            memories = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    memories.append({
                        'content': results['documents'][0][i],
                        'sender_name': results['metadatas'][0][i]['sender_name'],
                        'timestamp': results['metadatas'][0][i]['timestamp'],
                        'distance': results['distances'][0][i]
                    })
            
            logger.info(f"搜索记忆: {query[:30]}... → 找到 {len(memories)} 条")
            return memories
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total_memories': self.collection.count(),
            'collection_name': self.collection.name
        }
    
    def clear_all(self):
        """清空所有记忆（慎用）"""
        self.client.delete_collection("chat_memory")
        self.collection = self.client.get_or_create_collection(
            name="chat_memory",
            metadata={"description": "聊天记忆向量库"}
        )
        logger.warning("向量数据库已清空")


# 全局实例
_vector_store = None

def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
