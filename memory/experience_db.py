"""
本地经验向量数据库
=================
基于 ChromaDB 实现的轻量级本地经验记忆系统。
数据全部存储在本地文件中（项目根目录下的 experience_data/ 文件夹），无需任何云端服务。

工作流程：
  1. 每次项目完成后，自动将踩坑经验存入数据库
  2. 新项目启动时，PM Agent 自动检索相关历史经验作为参考
  3. 随着项目积累，经验库越来越丰富，系统越来越聪明
"""

import os
from datetime import datetime

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class ExperienceDB:
    """本地经验向量数据库（基于 ChromaDB）"""

    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: 数据库存储路径。
                     默认为项目根目录下的 experience_data/ 文件夹。
                     这是一个纯本地文件夹，不会上传到任何云端。
        """
        if not CHROMADB_AVAILABLE:
            print("  ⚠️ ChromaDB 未安装，经验记忆功能已禁用。")
            print("    安装命令: pip install chromadb")
            self.enabled = False
            return

        self.enabled = True
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "experience_data"
        )
        os.makedirs(self.db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="project_experiences",
            metadata={"description": "存储历史项目的开发经验与避坑指南"},
        )

    def save_experience(self, project_summary: str, project_name: str = "unnamed"):
        """
        存储一条项目经验。

        Args:
            project_summary: 项目总结文本（包含踩坑经验、最终方案、关键决策等）
            project_name: 项目名称（方便后续检索和管理）
        """
        if not self.enabled:
            return

        doc_id = f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.collection.add(
            documents=[project_summary],
            ids=[doc_id],
            metadatas=[{
                "project_name": project_name,
                "timestamp": datetime.now().isoformat(),
            }],
        )
        print(f"  💾 经验已存入本地数据库: {doc_id}")

    def search_experience(self, query: str, top_k: int = 3) -> list:
        """
        根据语义搜索相关历史经验。
        即使搜索词和存储的文字不完全一样，只要"意思"相近就能匹配到。

        Args:
            query: 搜索查询（自然语言描述，例如"做一个待办清单"）
            top_k: 返回最相关的前 N 条经验

        Returns:
            相关经验文本列表
        """
        if not self.enabled:
            return []

        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count()),
        )

        return results["documents"][0] if results["documents"] else []

    def list_all(self) -> int:
        """返回经验库中的记录总数"""
        if not self.enabled:
            return 0
        return self.collection.count()
