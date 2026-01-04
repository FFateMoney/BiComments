# BiComments

工程文档请参见 [`docs/ENGINEERING.md`](docs/ENGINEERING.md)。

## 快速开始
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

示例用法（需替换为真实登录态与用户 ID）：
```python
from bicomments.fetcher import Fetcher
from bicomments.interaction import PagedInteraction
from bicomments.orchestrator import Orchestrator
from bicomments.writer import InMemoryWriter

fetcher = Fetcher()
writer = InMemoryWriter()
interaction = PagedInteraction(max_pages=3)

Orchestrator(fetcher=fetcher, writer=writer, interaction=interaction).run_for_user("123456")
print(f\"videos={len(writer.videos)}, comments={len(writer.comments)}\")
```
