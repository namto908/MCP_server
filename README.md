# MCP Server

Đây là một server được xây dựng bằng **FastMCP**, cung cấp một tập hợp các công cụ để tương tác với nhiều dịch vụ và cơ sở dữ liệu khác nhau, bao gồm GitHub, Neo4j, PostgreSQL, và Milvus.

## Hướng dẫn Cài đặt và Chạy

Dự án này hỗ trợ hai kịch bản hoạt động chính:

1.  **Local Development (stdio):** Chạy server trực tiếp trên máy tính của bạn để phát triển và gỡ lỗi. Kết nối thông qua Standard I/O.
2.  **Remote Deployment (HTTP):** Triển khai server lên một máy chủ từ xa và truy cập qua mạng. Đây là kịch bản dành cho production.

---

### Kịch bản 1: Local Development (Chạy trên máy cá nhân)

Sử dụng kịch bản này khi bạn đang phát triển hoặc thử nghiệm các tính năng mới.

**1. Cài đặt:**

-   Clone repository về máy.
-   Tạo file `.env` và điền các thông tin cần thiết (xem mục **Cấu hình file .env** bên dưới).
-   Cài đặt các thư viện:
    ```bash
    uv pip install -r pyproject.toml
    ```

**2. Cấu hình mã nguồn:**

Đảm bảo dòng cuối cùng trong file `mcp_server.py` được đặt ở chế độ `stdio`:

```python
if __name__ == "__main__":
    mcp.run(transport='stdio')
```

**3. Cấu hình trong Claude Desktop (hoặc công cụ tương tự):**

Thêm một server mới với cấu hình chạy lệnh local:

-   **Command:** `D:\path\to\your\project\mcp_server\.venv\Scripts\uv.exe` (thay bằng đường dẫn thực tế)
-   **Arguments:** `run mcp_server.py`
-   **Working Directory:** `D:\path\to\your\project\mcp_server` (thay bằng đường dẫn thực tế)

---

### Kịch bản 2: Remote Deployment (Triển khai lên Server từ xa)

Sử dụng kịch bản này để đưa ứng dụng vào hoạt động và truy cập từ bất kỳ đâu.

**Bước 1: Chỉnh sửa mã nguồn để chạy ở chế độ HTTP**

Trong file `mcp_server.py`, thay đổi dòng cuối cùng để server chạy ở chế độ HTTP:

```python
if __name__ == "__main__":
    # Chạy server ở chế độ HTTP, lắng nghe trên tất cả các địa chỉ IP ở port 8000
    mcp.run(transport='http', host='0.0.0.0', port=8000)
```

**Bước 2: Đẩy code lên Git**

Đảm bảo file `.env` đã có trong `.gitignore` để không đưa thông tin nhạy cảm lên repository.

```bash
git add mcp_server.py
git commit -m "feat: Switch to HTTP transport for remote deployment"
git push origin main
```

**Bước 3: Chuẩn bị và Triển khai lên Server Remote (Ví dụ: Ubuntu)**

1.  **SSH vào server** và cài đặt các công cụ cần thiết:
    ```bash
    sudo apt update
    sudo apt install -y git python3 python3-pip
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Clone project** về server:
    ```bash
    git clone <your_repository_url>
    cd mcp_server
    ```

3.  **Cài đặt thư viện**:
    ```bash
    uv pip install -r pyproject.toml
    ```

4.  **Tạo file `.env` trên server** và điền các giá trị cấu hình cho môi trường production.
    ```bash
    nano .env
    ```

5.  **Mở port trên firewall** (ví dụ port 8000):
    ```bash
    sudo ufw allow 8000/tcp
    sudo ufw reload
    ```
    *Lưu ý: Nếu dùng AWS, GCP, Azure, bạn cần mở port trong Security Group/Network Rules.*

**Bước 4: Chạy ứng dụng như một Dịch vụ (Systemd)**

1.  Tạo file service:
    ```bash
    sudo nano /etc/systemd/system/mcp_server.service
    ```

2.  Dán nội dung sau vào file (thay `your_username` và đường dẫn cho đúng):
    ```ini
    [Unit]
    Description=MCP Server Application
    After=network.target

    [Service]
    User=your_username
    Group=your_username
    WorkingDirectory=/home/your_username/mcp_server
    ExecStart=/home/your_username/.cargo/bin/uv run /home/your_username/mcp_server/mcp_server.py
    Restart=always
    RestartSec=3

    [Install]
    WantedBy=multi-user.target
    ```

3.  Kích hoạt và khởi động service:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable mcp_server.service
    sudo systemctl start mcp_server.service
    ```

4.  Kiểm tra trạng thái:
    ```bash
    sudo systemctl status mcp_server.service
    ```

**Bước 5: Kết nối từ Claude Desktop**

Trong ứng dụng của bạn, thêm một server mới với cấu hình URL:

-   **Server URL:** `http://<your_remote_server_ip>:8000` (thay bằng IP public của server bạn).

---

## Cấu hình file .env

Tạo file `.env` trong thư mục gốc của dự án và điền các thông tin sau:

```env
# GitHub Personal Access Token
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Neo4j Connection Details
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="your_neo4j_password"

# PostgreSQL Connection Details
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="your_postgres_password"
POSTGRES_DB="your_database_name"

# Milvus Connection Details
MILVUS_HOST="localhost"
MILVUS_PORT="19530"
MILVUS_USER="your_milvus_user"
MILVUS_PASSWORD="your_milvus_password"
```

## Các Công Cụ Có Sẵn

-   `get_github_user_info()`
-   `get_github_repos()`
-   `run_neo4j_query(query: str)`
-   `run_postgres_query(query: str)`
-   `list_milvus_collections()`
-   `search_milvus_collection(...)`