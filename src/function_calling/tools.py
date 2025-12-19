"""
Tool Registry - Định nghĩa các tools/functions cho VNPT AI API
"""
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field


@dataclass
class ToolParameter:
    """Định nghĩa parameter của tool"""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    enum: Optional[List[Any]] = None


@dataclass
class Tool:
    """Định nghĩa một tool/function"""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    handler: Optional[Callable] = None  # Function thực thi tool
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """
        Convert sang format OpenAI function calling schema
        (VNPT AI có thể dùng format tương tự)
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class ToolRegistry:
    """
    Registry quản lý các tools và mapping với handlers
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._setup_default_tools()
    
    def _setup_default_tools(self):
        """Khởi tạo các tools mặc định"""
        
        # Tool 1: Giải toán học
        self.register(Tool(
            name="solve_math_problem",
            description=(
                "Giải các bài toán toán học, vật lý, hóa học. "
                "Sử dụng tool này khi user yêu cầu tính toán, giải phương trình, "
                "hoặc giải các bài toán khoa học."
            ),
            parameters=[
                ToolParameter(
                    name="problem_statement",
                    type="string",
                    description="Phát biểu đầy đủ của bài toán cần giải"
                ),
                ToolParameter(
                    name="problem_type",
                    type="string",
                    description="Loại bài toán",
                    enum=[
                        "math",         # Toán học (đại số, hình học, giải tích)
                        "physics",      # Vật lý
                        "chemistry",    # Hóa học
                        "economics",    # Kinh tế (co giãn, chi phí, lãi suất...)
                        "statistics",   # Thống kê (giả thuyết, kiểm định...)
                        "calculus",     # Giải tích (đạo hàm, tích phân, vi phân...)
                        "logic",        # Logic và reasoning
                        "other"         # Loại khác
                    ]
                ),
                ToolParameter(
                    name="given_options",
                    type="array",
                    description="Các phương án lựa chọn (nếu là trắc nghiệm)",
                    required=False
                )
            ]
        ))
        
        # Tool 2: Tra cứu thông tin từ RAG
        self.register(Tool(
            name="search_knowledge_base",
            description=(
                "Tìm kiếm thông tin từ cơ sở dữ liệu văn bản pháp luật, "
                "tài liệu chính thức. Sử dụng khi user hỏi về quy định, "
                "nghị định, luật, thông tư, hoặc bất kỳ thông tin nào "
                "có trong knowledge base."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Câu hỏi hoặc từ khóa cần tìm kiếm"
                ),
                ToolParameter(
                    name="top_k",
                    type="number",
                    description="Số lượng kết quả trả về (mặc định: 3)",
                    required=False
                ),
                ToolParameter(
                    name="doc_type",
                    type="string",
                    description="Loại văn bản cần tìm",
                    enum=["nghị định", "thông tư", "luật", "quyết định", "all"],
                    required=False
                )
            ]
        ))
        
        # Tool 3: Calculator đơn giản
        self.register(Tool(
            name="calculate",
            description="Thực hiện các phép tính toán học cơ bản",
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="Biểu thức toán học cần tính (ví dụ: '2 + 2 * 3')"
                )
            ]
        ))
        
        # Tool 4: Use embedded context (for queries with pre-existing knowledge)
        self.register(Tool(
            name="use_embedded_context",
            description=(
                "Sử dụng context/thông tin có sẵn trong câu hỏi. "
                "Dùng khi user đã cung cấp đầy đủ thông tin/đoạn văn trong query, "
                "không cần tìm kiếm thêm từ database."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Câu hỏi cần trả lời"
                ),
                ToolParameter(
                    name="full_text",
                    type="string",
                    description="Toàn bộ text bao gồm context và câu hỏi"
                )
            ]
        ))
    
    def register(self, tool: Tool):
        """Đăng ký tool mới"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Lấy tool theo tên"""
        return self.tools.get(name)
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        Lấy tất cả tool schemas để gửi cho VNPT AI API
        """
        return [tool.to_openai_schema() for tool in self.tools.values()]
    
    def get_tools_for_intent(self, intent: str) -> List[Dict[str, Any]]:
        """
        Lấy tools phù hợp với intent cụ thể
        Điều này giúp giảm context và tăng accuracy
        """
        intent_tool_mapping = {
            "math": ["solve_math_problem", "calculate"],
            "rag": ["search_knowledge_base"],
            "general": []  # Không cần tools
        }
        
        tool_names = intent_tool_mapping.get(intent, [])
        return [
            self.tools[name].to_openai_schema() 
            for name in tool_names 
            if name in self.tools
        ]
    
    def bind_handler(self, tool_name: str, handler: Callable):
        """
        Gắn handler function vào tool
        
        Args:
            tool_name: Tên của tool
            handler: Function xử lý khi tool được gọi
        """
        if tool_name in self.tools:
            self.tools[tool_name].handler = handler
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Thực thi tool với arguments
        
        Args:
            tool_name: Tên tool cần gọi
            **kwargs: Arguments cho tool
            
        Returns:
            Kết quả từ handler
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        if not tool.handler:
            raise ValueError(f"Tool '{tool_name}' has no handler")
        
        return tool.handler(**kwargs)


# if __name__ == "__main__":
#     # Test registry
#     registry = ToolRegistry()
    
#     print("All registered tools:")
#     for name, tool in registry.tools.items():
#         print(f"\n  • {name}")
#         print(f"    {tool.description[:80]}...")
    
#     print("\n\n OpenAI Schema format:")
#     import json
#     schemas = registry.get_all_schemas()
#     print(json.dumps(schemas[0], indent=2, ensure_ascii=False))
    
#     print("\n\n Tools for 'math' intent:")
#     math_tools = registry.get_tools_for_intent("math")
#     print([t["function"]["name"] for t in math_tools])
