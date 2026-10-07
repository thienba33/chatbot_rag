# Chatbot RAG Base

Chatbot hỏi đáp bằng tiếng Việt dựa trên tài liệu PDF, dùng LangChain để kết nối các bước đọc tài liệu, chia đoạn, tìm kiếm và tạo câu trả lời. Dữ liệu mẫu của dự án là các hợp đồng thuê phòng.

Ứng dụng chạy trong terminal. Mỗi lần chạy, chương trình nạp tài liệu, nhận một câu hỏi, in câu trả lời rồi kết thúc.

## Luồng xử lý

```text
PDF trong data/ → PyPDFLoader → Chia chunk → Google Embedding → Chroma
                                                                  ↑
Câu hỏi → Embedding câu hỏi → Tìm kiếm và lọc theo ngưỡng ───────────┘
                                      ↓
                        Các chunk + câu hỏi + prompt
                                      ↓
                                Gemini LLM
                                      ↓
                          Câu trả lời tiếng Việt
```

Prompt yêu cầu chatbot chỉ trả lời theo tài liệu được truy xuất, trích dẫn theo dạng `(source:page)` và thông báo khi không đủ thông tin. Đây là hướng dẫn cho model, không phải cơ chế bảo đảm mọi câu trả lời hay trích dẫn đều chính xác.

## Công nghệ

| Thành phần | Công nghệ |
| --- | --- |
| Điều phối luồng RAG | LangChain |
| Đọc PDF | `PyPDFLoader`, `pypdf` |
| Chia văn bản | `RecursiveCharacterTextSplitter` |
| Embedding | `GoogleGenerativeAIEmbeddings` |
| Vector database | Chroma, lưu trên máy |
| LLM | `ChatGoogleGenerativeAI` |
| Cấu hình môi trường | `python-dotenv` |

## Cấu trúc dự án

```text
chatbot_rag/
├── main.py       # Nạp tài liệu, tạo vector store và chạy hỏi đáp
├── prompt.py     # Hướng dẫn trả lời và trích dẫn
├── data/         # Đặt các tài liệu PDF tại đây
├── chroma_db/    # Dữ liệu Chroma được tạo khi chạy
├── .env          # API key tự cấu hình trên máy
└── README.md
```

## Cài đặt

Cần Python, `pip`, khả năng tạo môi trường `venv` và kết nối Internet để gọi API Google. Môi trường phát triển hiện tại dùng Python 3.14; dự án chưa có file khóa phiên bản thư viện.

Chạy các lệnh sau tại thư mục dự án trên Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install langchain-community langchain-text-splitters langchain-google-genai langchain-core langchain-chroma chromadb pypdf python-dotenv tqdm
```

Trên Windows PowerShell, kích hoạt venv bằng:

```powershell
.venv\Scripts\Activate.ps1
```

Luồng đọc PDF hiện tại không cần `unstructured[pdf]`, PyTorch hay FAISS.

## Cấu hình Google API key

Tạo API key tại [Google AI Studio](https://aistudio.google.com/apikey), sau đó tạo file `.env` trong thư mục dự án:

```dotenv
GOOGLE_API_KEY=your_google_api_key
```

Thay giá trị mẫu bằng key thật. Không đưa `.env` lên Git hoặc chia sẻ API key. Dữ liệu văn bản được gửi tới Google để tạo embedding và sinh câu trả lời; Chroma lưu vector trên máy.

Model đang được khai báo trong `main.py`:

```python
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash"
)
```

Đây là cấu hình của code hiện tại. Model cần khả dụng với API key và project của bạn. Kiểm tra hạn mức và chế độ thanh toán trong Google AI Studio; dự án không bảo đảm các lời gọi API đều miễn phí.

## Chuẩn bị tài liệu và chạy

1. Đặt PDF vào thư mục `data/`. Chương trình tìm cả PDF trong các thư mục con.
2. Dùng PDF có lớp văn bản; luồng hiện tại chưa cấu hình OCR cho bản scan chỉ chứa ảnh.
3. Kích hoạt venv và chạy từ thư mục gốc của dự án:

```bash
source .venv/bin/activate
python main.py
```

Nhập câu hỏi khi terminal hiển thị `Question:`, ví dụ:

```text
Question: Tiền đặt cọc phòng A101 là bao nhiêu?
```

Chương trình truy xuất các đoạn liên quan rồi in câu trả lời của Gemini. Hiện tại ứng dụng chưa có vòng lặp hội thoại, lịch sử trò chuyện hoặc streaming.

## Cấu hình truy xuất

Các giá trị hiện tại trong `main.py`:

| Tham số | Giá trị | Ý nghĩa |
| --- | --- | --- |
| `chunk_size` | `1200` | Kích thước chunk tính theo ký tự |
| `chunk_overlap` | `200` | Mức chồng lặp mục tiêu giữa các chunk |
| `collection_name` | `My_document` | Tên collection trong Chroma |
| `persist_directory` | `./chroma_db` | Thư mục lưu dữ liệu |
| `hnsw.space` | `cosine` | Phép đo khoảng cách khi tạo collection mới |
| `search_type` | `similarity_score_threshold` | Lọc kết quả theo ngưỡng điểm liên quan |
| `k` | `5` | Số chunk ứng viên tối đa |
| `score_threshold` | `0.2` | Ngưỡng điểm để giữ lại chunk |

```python
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 5, "score_threshold": 0.2},
)
```

Điểm `0.2` không có nghĩa là độ chính xác 20%. Cần thử với các câu hỏi có đáp án biết trước để điều chỉnh ngưỡng. Nếu không có chunk đạt ngưỡng, retriever có thể trả về danh sách rỗng.

## Tài liệu tham khảo

- [LangChain – Chroma](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma)
- [LangChain – Google GenAI](https://reference.langchain.com/python/langchain-google-genai)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [Chroma](https://docs.trychroma.com/)
