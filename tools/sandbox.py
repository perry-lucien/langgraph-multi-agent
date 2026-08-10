"""
Docker 沙盒代码执行器
=====================
在 Docker 容器中安全地执行代码，捕获真实的终端输出（stdout/stderr）。
QA 测试子代理通过此工具进行物理代码验证。

如果 Docker 不可用，会自动回退到"本地文件夹隔离"方案。
"""

import os
import shutil
import subprocess
import tempfile

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class DockerSandbox:
    """
    Docker 容器沙盒执行器（推荐方案）
    代码在完全隔离的容器中运行，不会影响宿主机。
    """

    def __init__(self, timeout: int = 30, image: str = "python:3.11-slim"):
        """
        Args:
            timeout: 代码执行超时时间（秒），防止死循环代码卡住
            image: Docker 基础镜像名称
        """
        self.timeout = timeout
        self.image = image
        self.client = docker.from_env()

    def execute_code(self, files: dict, entry_command: str = "python main.py") -> dict:
        """
        在 Docker 容器中执行代码。

        Args:
            files: 要写入容器的文件，格式 {"文件名": "文件内容"}
                   例: {"main.py": "print('hello')", "utils.py": "def add(a,b): return a+b"}
            entry_command: 入口执行命令

        Returns:
            {"success": bool, "stdout": str, "stderr": str, "exit_code": int}
        """
        # 创建临时目录，写入代码文件
        tmp_dir = tempfile.mkdtemp(prefix="agent_sandbox_")

        try:
            for filename, content in files.items():
                filepath = os.path.join(tmp_dir, filename)
                # 确保子目录存在
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

            # 启动 Docker 容器执行代码
            container = self.client.containers.run(
                image=self.image,
                command=f'sh -c "{entry_command}"',
                volumes={tmp_dir: {"bind": "/code", "mode": "rw"}},
                working_dir="/code",
                detach=True,
                mem_limit="256m",        # 限制内存 256MB，防止代码吃光内存
                network_mode="none",     # 禁用网络，防止恶意代码外联
            )

            # 等待执行完成（带超时保护）
            try:
                result = container.wait(timeout=self.timeout)
                exit_code = result.get("StatusCode", -1)
            except Exception:
                # 超时则强制杀死容器
                container.kill()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"⏰ 执行超时！代码运行超过 {self.timeout} 秒，已被强制终止。"
                             f"可能原因：死循环、阻塞式等待、或计算量过大。",
                    "exit_code": -1,
                }

            # 收集输出
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            # 清理容器
            container.remove(force=True)

            return {
                "success": exit_code == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
            }

        finally:
            # 无论成功失败，都清理临时文件
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def health_check(self) -> bool:
        """检查 Docker 引擎是否可用"""
        try:
            self.client.ping()
            return True
        except Exception:
            return False


class LocalSandbox:
    """
    本地文件夹隔离沙盒（Docker 不可用时的回退方案）
    ⚠️ 安全性较低，仅建议在开发测试阶段使用。
    代码在项目的 sandbox/ 子目录中运行。
    """

    def __init__(self, timeout: int = 30, sandbox_dir: str = None):
        """
        Args:
            timeout: 代码执行超时时间（秒）
            sandbox_dir: 沙盒目录路径，默认为项目根目录下的 sandbox/
        """
        self.timeout = timeout
        self.sandbox_dir = sandbox_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "sandbox"
        )
        os.makedirs(self.sandbox_dir, exist_ok=True)

    def execute_code(self, files: dict, entry_command: str = "python main.py") -> dict:
        """
        在本地隔离目录中执行代码。

        Args:
            files: 要写入沙盒的文件，格式 {"文件名": "文件内容"}
            entry_command: 入口执行命令

        Returns:
            {"success": bool, "stdout": str, "stderr": str, "exit_code": int}
        """
        # 清空沙盒目录（防止上次残留文件干扰）
        for f in os.listdir(self.sandbox_dir):
            fp = os.path.join(self.sandbox_dir, f)
            if os.path.isfile(fp):
                os.remove(fp)
            elif os.path.isdir(fp):
                shutil.rmtree(fp, ignore_errors=True)

        # 写入代码文件
        for filename, content in files.items():
            filepath = os.path.join(self.sandbox_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        # 执行代码
        try:
            result = subprocess.run(
                entry_command,
                shell=True,
                cwd=self.sandbox_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"⏰ 执行超时！代码运行超过 {self.timeout} 秒，已被强制终止。",
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行异常: {str(e)}",
                "exit_code": -1,
            }


def get_sandbox():
    """
    智能选择沙盒引擎：优先使用 Docker，不可用时自动回退到本地沙盒。
    """
    if DOCKER_AVAILABLE:
        try:
            sandbox = DockerSandbox()
            if sandbox.health_check():
                print("  🐳 Docker 沙盒已就绪")
                return sandbox
        except Exception:
            pass

    print("  ⚠️ Docker 不可用，已回退至本地文件夹沙盒（安全性较低）")
    return LocalSandbox()
