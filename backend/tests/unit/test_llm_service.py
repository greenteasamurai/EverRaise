import pytest
import asyncio
from app.services.llm import LLMService, LLMRequest, LLMResponse

@pytest.fixture
def llm_service():
    """
    Create an LLM service instance for testing.
    """
    return LLMService()

def test_count_tokens(llm_service):
    """
    Test that token counting functionality works properly.
    """
    # Test with empty string
    assert llm_service._count_tokens("") == 0
    
    # Test with a simple sentence
    text = "This is a test sentence."
    token_count = llm_service._count_tokens(text)
    assert token_count > 0, "Token count should be greater than 0"
    assert isinstance(token_count, int), "Token count should be an integer"
    
    # Test with a longer text
    longer_text = "This is a much longer text that should have more tokens. " * 10
    longer_token_count = llm_service._count_tokens(longer_text)
    assert longer_token_count > token_count, "Longer text should have more tokens"

@pytest.mark.asyncio
async def test_generate_text_mock(monkeypatch, llm_service):
    """
    Test the generate_text method using a mocked _call_ollama method.
    """
    # Mock response
    mock_response = LLMResponse(
        text="This is a test response from the LLM service.",
        model="test-model",
        token_usage={
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20
        }
    )
    
    # Create a mock for _call_ollama
    async def mock_call_ollama(*args, **kwargs):
        return mock_response
    
    # Apply the mock
    monkeypatch.setattr(llm_service, "_call_ollama", mock_call_ollama)
    
    # Create a test request
    request = LLMRequest(
        prompt="Test prompt",
        model="test-model",
        temperature=0.5,
        max_tokens=100
    )
    
    # Call the method
    response = await llm_service.generate_text(request)
    
    # Verify the response
    assert response == mock_response
    assert response.text == "This is a test response from the LLM service."
    assert response.model == "test-model"
    assert response.token_usage["total_tokens"] == 20

@pytest.mark.asyncio
async def test_create_vectorstore_from_texts(llm_service, monkeypatch):
    """
    Test creating a vector store from texts.
    """
    # Create test data
    texts = [
        {
            "content": "This is test content 1",
            "metadata": {"source": "test1", "date": "2023-01-01"}
        },
        {
            "content": "This is test content 2",
            "metadata": {"source": "test2", "date": "2023-01-02"}
        }
    ]
    
    # Create simple mock for Chroma that just returns a new instance
    class MockChroma:
        @classmethod
        def from_documents(cls, **kwargs):
            return MockChroma()
            
        def as_retriever(self, **kwargs):
            return None
    
    # Mock for OllamaEmbeddings
    class MockOllamaEmbeddings:
        def __init__(self, **kwargs):
            pass

    # Mock document splitter
    class MockSplitter:
        def create_documents(self, documents, metadatas=None):
            return documents
    
    # Mock the dependencies
    monkeypatch.setattr("app.services.llm.Chroma", MockChroma)
    monkeypatch.setattr("app.services.llm.OllamaEmbeddings", MockOllamaEmbeddings)
    monkeypatch.setattr("app.services.llm.RecursiveCharacterTextSplitter", lambda **kwargs: MockSplitter())
    
    # Also mock the filter function
    def mock_filter(data):
        return data
    monkeypatch.setattr("app.services.llm.filter_complex_metadata", mock_filter)
    
    # Call the method
    result = llm_service.create_vectorstore_from_texts(texts)
    
    # Simple check that the mocking worked
    assert isinstance(result, MockChroma) 