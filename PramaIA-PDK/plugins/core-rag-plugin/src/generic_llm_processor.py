"""
Generic LLM Processor

Processore universale per Large Language Models: OpenAI, Anthropic, Ollama, Hugging Face.
Supporta prompt templating, response formatting, conversation management e provider switching.
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable
from abc import ABC, abstractmethod
from datetime import datetime
import hashlib
import re

logger = logging.getLogger(__name__)


# ============================================================================
# Abstract Interfaces for LLM Operations
# ============================================================================

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response using the LLM provider."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of supported models."""
        pass
    
    @abstractmethod
    def get_max_context_length(self, model: str) -> int:
        """Get maximum context length for model."""
        pass


class PromptTemplate(ABC):
    """Abstract base class for prompt templates."""
    
    @abstractmethod
    async def format(self, template: str, context: Dict[str, Any]) -> str:
        """Format prompt template with context."""
        pass


class ResponseFormatter(ABC):
    """Abstract base class for response formatters."""
    
    @abstractmethod
    async def format(self, response: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Format LLM response according to configuration."""
        pass


# ============================================================================
# Concrete LLM Provider Implementations
# ============================================================================

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self):
        self.client = None
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import openai
            return True
        except ImportError:
            logger.warning("⚠️ OpenAI library not available")
            return False
    
    def get_supported_models(self) -> List[str]:
        return [
            'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 
            'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'
        ] if self.is_available else []
    
    def get_max_context_length(self, model: str) -> int:
        context_lengths = {
            'gpt-4o': 128000,
            'gpt-4o-mini': 128000,
            'gpt-4-turbo': 128000,
            'gpt-4': 8192,
            'gpt-3.5-turbo': 16385,
            'gpt-3.5-turbo-16k': 16385
        }
        return context_lengths.get(model, 4096)
    
    async def generate(self, messages: List[Dict[str, str]], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available:
            return await self._mock_generate(messages, config)
        
        try:
            import openai
            
            # Initialize client if needed
            if not self.client:
                api_key = config.get('api_key', config.get('openai_api_key'))
                if not api_key:
                    raise ValueError("OpenAI API key not provided")
                self.client = openai.OpenAI(api_key=api_key)
            
            model = config.get('model', 'gpt-3.5-turbo')
            max_tokens = config.get('max_tokens', 1000)
            temperature = config.get('temperature', 0.7)
            top_p = config.get('top_p', 1.0)
            frequency_penalty = config.get('frequency_penalty', 0.0)
            presence_penalty = config.get('presence_penalty', 0.0)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )
            
            return {
                'content': response.choices[0].message.content,
                'model': model,
                'provider': 'openai',
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'finish_reason': response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return await self._mock_generate(messages, config, f"OpenAI error: {e}")
    
    async def _mock_generate(self, messages: List[Dict[str, str]], config: Dict[str, Any], error_msg: str = "") -> Dict[str, Any]:
        """Mock generation for testing or when API is unavailable."""
        content = f"[Mock OpenAI Response{': ' + error_msg if error_msg else ''}]\n\n"
        
        # Extract user query from messages
        user_messages = [msg['content'] for msg in messages if msg.get('role') == 'user']
        if user_messages:
            content += f"Based on your query: {user_messages[-1][:100]}...\n\n"
        
        content += """This is a mock response from the OpenAI provider. In production, this would be generated by a real GPT model with comprehensive understanding and reasoning capabilities.

Key features that would be available:
- Advanced natural language understanding
- Contextual reasoning and analysis
- Multi-turn conversation handling
- Domain-specific knowledge
- Creative and analytical thinking"""
        
        estimated_tokens = sum(len(msg['content'].split()) for msg in messages)
        
        return {
            'content': content,
            'model': config.get('model', 'gpt-3.5-turbo'),
            'provider': 'openai',
            'usage': {
                'prompt_tokens': estimated_tokens,
                'completion_tokens': len(content.split()),
                'total_tokens': estimated_tokens + len(content.split())
            },
            'finish_reason': 'stop',
            'mock': True
        }


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self):
        self.client = None
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import anthropic
            return True
        except ImportError:
            logger.warning("⚠️ Anthropic library not available")
            return False
    
    def get_supported_models(self) -> List[str]:
        return [
            'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022',
            'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 
            'claude-3-haiku-20240307'
        ] if self.is_available else []
    
    def get_max_context_length(self, model: str) -> int:
        # Most Claude models support 200k tokens
        return 200000 if 'claude-3' in model else 100000
    
    async def generate(self, messages: List[Dict[str, str]], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available:
            return await self._mock_generate(messages, config)
        
        try:
            import anthropic
            
            # Initialize client if needed
            if not self.client:
                api_key = config.get('api_key', config.get('anthropic_api_key'))
                if not api_key:
                    raise ValueError("Anthropic API key not provided")
                self.client = anthropic.Anthropic(api_key=api_key)
            
            model = config.get('model', 'claude-3-5-sonnet-20241022')
            max_tokens = config.get('max_tokens', 1000)
            temperature = config.get('temperature', 0.7)
            
            # Extract system message if present
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg.get('role') == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=model,
                system=system_message if system_message else None,
                messages=user_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                'content': response.content[0].text,
                'model': model,
                'provider': 'anthropic',
                'usage': {
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                'finish_reason': response.stop_reason
            }
            
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            return await self._mock_generate(messages, config, f"Anthropic error: {e}")
    
    async def _mock_generate(self, messages: List[Dict[str, str]], config: Dict[str, Any], error_msg: str = "") -> Dict[str, Any]:
        """Mock generation for testing or when API is unavailable."""
        content = f"[Mock Claude Response{': ' + error_msg if error_msg else ''}]\n\n"
        
        # Extract user query from messages
        user_messages = [msg['content'] for msg in messages if msg.get('role') == 'user']
        if user_messages:
            content += f"Regarding your question: {user_messages[-1][:100]}...\n\n"
        
        content += """This is a mock response from the Anthropic Claude provider. In production, this would be generated by Claude with its advanced reasoning and analytical capabilities.

Claude's key strengths include:
- Thoughtful and nuanced analysis
- Strong ethical reasoning
- Excellent at understanding context and subtext
- Helpful, harmless, and honest responses
- Advanced reasoning about complex topics"""
        
        estimated_tokens = sum(len(msg['content'].split()) for msg in messages)
        
        return {
            'content': content,
            'model': config.get('model', 'claude-3-5-sonnet-20241022'),
            'provider': 'anthropic',
            'usage': {
                'prompt_tokens': estimated_tokens,
                'completion_tokens': len(content.split()),
                'total_tokens': estimated_tokens + len(content.split())
            },
            'finish_reason': 'end_turn',
            'mock': True
        }


class OllamaProvider(LLMProvider):
    """Ollama local models provider."""
    
    def __init__(self):
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import requests
            # Try to ping Ollama server
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            logger.warning("⚠️ Ollama server not available")
            return False
    
    def get_supported_models(self) -> List[str]:
        if not self.is_available:
            return []
        
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except:
            pass
        
        # Fallback to common models
        return ['llama2', 'llama2:13b', 'codellama', 'mistral', 'neural-chat']
    
    def get_max_context_length(self, model: str) -> int:
        # Most Ollama models support 4k tokens, some newer ones support more
        if 'llama2' in model.lower():
            return 4096
        elif 'mistral' in model.lower():
            return 8192
        else:
            return 4096
    
    async def generate(self, messages: List[Dict[str, str]], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available:
            return await self._mock_generate(messages, config)
        
        try:
            import requests
            
            model = config.get('model', 'llama2')
            temperature = config.get('temperature', 0.7)
            max_tokens = config.get('max_tokens', 1000)
            
            # Convert messages to prompt for Ollama
            prompt = self._messages_to_prompt(messages)
            
            ollama_url = config.get('ollama_url', 'http://localhost:11434')
            
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json=payload,
                timeout=config.get('timeout', 60)
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    'content': result.get('response', ''),
                    'model': model,
                    'provider': 'ollama',
                    'usage': {
                        'prompt_tokens': result.get('prompt_eval_count', 0),
                        'completion_tokens': result.get('eval_count', 0),
                        'total_tokens': result.get('prompt_eval_count', 0) + result.get('eval_count', 0)
                    },
                    'finish_reason': 'stop' if result.get('done', False) else 'length'
                }
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return await self._mock_generate(messages, config, f"Ollama error: {e}")
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to single prompt."""
        prompt_parts = []
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    async def _mock_generate(self, messages: List[Dict[str, str]], config: Dict[str, Any], error_msg: str = "") -> Dict[str, Any]:
        """Mock generation when Ollama is not available."""
        content = f"[Mock Ollama Response{': ' + error_msg if error_msg else ''}]\n\n"
        
        user_messages = [msg['content'] for msg in messages if msg.get('role') == 'user']
        if user_messages:
            content += f"Processing your request: {user_messages[-1][:100]}...\n\n"
        
        content += """This is a mock response from an Ollama local model. In production, this would be generated by a locally-running open source model.

Benefits of local models:
- Privacy: Your data stays on your machine
- No API costs or rate limits
- Offline capability
- Customization and fine-tuning options
- Full control over the model"""
        
        estimated_tokens = sum(len(msg['content'].split()) for msg in messages)
        
        return {
            'content': content,
            'model': config.get('model', 'llama2'),
            'provider': 'ollama',
            'usage': {
                'prompt_tokens': estimated_tokens,
                'completion_tokens': len(content.split()),
                'total_tokens': estimated_tokens + len(content.split())
            },
            'finish_reason': 'stop',
            'mock': True
        }


class HuggingFaceProvider(LLMProvider):
    """Hugging Face Transformers provider."""
    
    def __init__(self):
        self.pipeline = None
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import transformers
            import torch
            return True
        except ImportError:
            logger.warning("⚠️ Transformers library not available")
            return False
    
    def get_supported_models(self) -> List[str]:
        return [
            'microsoft/DialoGPT-medium',
            'facebook/blenderbot-400M-distill',
            'microsoft/DialoGPT-small',
            'gpt2', 'gpt2-medium', 'gpt2-large'
        ] if self.is_available else []
    
    def get_max_context_length(self, model: str) -> int:
        context_lengths = {
            'gpt2': 1024,
            'gpt2-medium': 1024,
            'gpt2-large': 1024,
            'microsoft/DialoGPT-medium': 1024,
            'facebook/blenderbot-400M-distill': 512
        }
        return context_lengths.get(model, 512)
    
    async def generate(self, messages: List[Dict[str, str]], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available:
            return await self._mock_generate(messages, config)
        
        try:
            import transformers
            
            model_name = config.get('model', 'microsoft/DialoGPT-medium')
            max_tokens = config.get('max_tokens', 100)
            temperature = config.get('temperature', 0.7)
            
            # Initialize pipeline if needed
            if not self.pipeline or self.pipeline.model.config.name_or_path != model_name:
                self.pipeline = transformers.pipeline(
                    'text-generation',
                    model=model_name,
                    device=0 if config.get('use_gpu', False) else -1
                )
            
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            # Generate response
            outputs = self.pipeline(
                prompt,
                max_length=len(prompt.split()) + max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.pipeline.tokenizer.eos_token_id
            )
            
            generated_text = outputs[0]['generated_text']
            # Extract only the new part
            response_text = generated_text[len(prompt):].strip()
            
            return {
                'content': response_text,
                'model': model_name,
                'provider': 'huggingface',
                'usage': {
                    'prompt_tokens': len(prompt.split()),
                    'completion_tokens': len(response_text.split()),
                    'total_tokens': len(prompt.split()) + len(response_text.split())
                },
                'finish_reason': 'stop'
            }
            
        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
            return await self._mock_generate(messages, config, f"HuggingFace error: {e}")
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to prompt format."""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                prompt_parts.append(content)
            elif role == 'assistant':
                prompt_parts.append(content)
        return " ".join(prompt_parts)
    
    async def _mock_generate(self, messages: List[Dict[str, str]], config: Dict[str, Any], error_msg: str = "") -> Dict[str, Any]:
        """Mock generation when transformers is not available."""
        content = f"[Mock HuggingFace Response{': ' + error_msg if error_msg else ''}]\n\n"
        
        user_messages = [msg['content'] for msg in messages if msg.get('role') == 'user']
        if user_messages:
            content += f"Understanding your input: {user_messages[-1][:100]}...\n\n"
        
        content += """This is a mock response from a HuggingFace Transformers model. In production, this would be generated by an open source model running locally.

HuggingFace advantages:
- Vast model library
- Easy model switching
- Local inference
- Fine-tuning capabilities
- Open source transparency"""
        
        estimated_tokens = sum(len(msg['content'].split()) for msg in messages)
        
        return {
            'content': content,
            'model': config.get('model', 'gpt2'),
            'provider': 'huggingface',
            'usage': {
                'prompt_tokens': estimated_tokens,
                'completion_tokens': len(content.split()),
                'total_tokens': estimated_tokens + len(content.split())
            },
            'finish_reason': 'stop',
            'mock': True
        }


# ============================================================================
# Concrete Prompt Template Implementations
# ============================================================================

class SimplePromptTemplate(PromptTemplate):
    """Simple string-based prompt template."""
    
    async def format(self, template: str, context: Dict[str, Any]) -> str:
        """Format template with simple string substitution."""
        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template


class JinjaPromptTemplate(PromptTemplate):
    """Jinja2-based prompt template (if available)."""
    
    def __init__(self):
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import jinja2
            return True
        except ImportError:
            return False
    
    async def format(self, template: str, context: Dict[str, Any]) -> str:
        """Format template using Jinja2."""
        if not self.is_available:
            # Fallback to simple template
            simple = SimplePromptTemplate()
            return await simple.format(template, context)
        
        try:
            import jinja2
            jinja_template = jinja2.Template(template)
            return jinja_template.render(**context)
        except Exception as e:
            logger.error(f"Jinja2 template error: {e}")
            return template


# ============================================================================
# Concrete Response Formatter Implementations  
# ============================================================================

class DetailedResponseFormatter(ResponseFormatter):
    """Detailed response formatting with metadata."""
    
    async def format(self, response: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        include_metadata = config.get('include_metadata', True)
        include_usage = config.get('include_usage', True)
        max_length = config.get('max_response_length', 0)
        
        content = response.get('content', '')
        
        # Truncate if needed
        if max_length > 0 and len(content) > max_length:
            content = content[:max_length] + "..."
        
        formatted = {
            'response': content,
            'timestamp': datetime.now().isoformat()
        }
        
        if include_metadata:
            formatted['metadata'] = {
                'provider': response.get('provider', 'unknown'),
                'model': response.get('model', 'unknown'),
                'finish_reason': response.get('finish_reason', 'unknown'),
                'response_length': len(content)
            }
        
        if include_usage and 'usage' in response:
            formatted['usage'] = response['usage']
        
        return formatted


class SimpleResponseFormatter(ResponseFormatter):
    """Simple response formatting - content only."""
    
    async def format(self, response: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        max_length = config.get('max_response_length', 0)
        content = response.get('content', '')
        
        if max_length > 0 and len(content) > max_length:
            content = content[:max_length] + "..."
        
        return {'response': content}


class MarkdownResponseFormatter(ResponseFormatter):
    """Markdown-formatted response."""
    
    async def format(self, response: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        content = response.get('content', '')
        provider = response.get('provider', 'unknown')
        model = response.get('model', 'unknown')
        
        markdown = f"""# AI Response

**Provider:** {provider}  
**Model:** {model}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{content}
"""
        
        if 'usage' in response:
            usage = response['usage']
            markdown += f"""
---

**Token Usage:**
- Prompt tokens: {usage.get('prompt_tokens', 0)}
- Completion tokens: {usage.get('completion_tokens', 0)} 
- Total tokens: {usage.get('total_tokens', 0)}
"""
        
        return {'response': markdown, 'format': 'markdown'}


# ============================================================================
# Main Generic LLM Processor
# ============================================================================

class GenericLLMProcessor:
    """Universal LLM processor supporting multiple providers and configurations."""
    
    def __init__(self):
        # Registry of available providers
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'ollama': OllamaProvider(),
            'huggingface': HuggingFaceProvider()
        }
        
        # Registry of prompt templates
        self.templates = {
            'simple': SimplePromptTemplate(),
            'jinja': JinjaPromptTemplate()
        }
        
        # Registry of response formatters
        self.formatters = {
            'detailed': DetailedResponseFormatter(),
            'simple': SimpleResponseFormatter(),
            'markdown': MarkdownResponseFormatter()
        }
        
        # Conversation history for multi-turn conversations
        self.conversations = {}
    
    async def process(self, context) -> Dict[str, Any]:
        """Main processing method."""
        logger.info("[GenericLLMProcessor] INGRESSO nodo: process")
        
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            
            operation = config.get('operation', 'generate')
            
            if operation == 'generate':
                return await self._process_generation(inputs, config)
            elif operation == 'chat':
                return await self._process_conversation(inputs, config)
            elif operation == 'template':
                return await self._process_templating(inputs, config)
            elif operation == 'format':
                return await self._process_formatting(inputs, config)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"[GenericLLMProcessor] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "operation": config.get('operation', 'unknown'),
                "output": None
            }
    
    async def _process_generation(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process single-turn text generation."""
        # Get input content
        user_prompt = inputs.get('prompt', inputs.get('query', inputs.get('text', '')))
        system_prompt = inputs.get('system_prompt', config.get('system_prompt', ''))
        context_data = inputs.get('context', inputs.get('documents', {}))
        
        if not user_prompt:
            raise ValueError("No prompt provided for generation")
        
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Apply prompt template if specified
        template_name = config.get('template', 'simple')
        template_str = config.get('prompt_template', '{prompt}')
        
        if template_name in self.templates:
            template_engine = self.templates[template_name]
            formatted_prompt = await template_engine.format(
                template_str, 
                {'prompt': user_prompt, 'context': context_data, **inputs}
            )
        else:
            formatted_prompt = user_prompt
        
        messages.append({"role": "user", "content": formatted_prompt})
        
        # Generate response
        provider_name = config.get('provider', 'openai')
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        response = await provider.generate(messages, config)
        
        # Format response
        formatter_name = config.get('response_format', 'detailed')
        formatter = self.formatters.get(formatter_name, self.formatters['detailed'])
        formatted_response = await formatter.format(response, config)
        
        logger.info(f"[GenericLLMProcessor] USCITA generation (successo): {provider_name} response generated")
        return {
            "status": "success",
            "operation": "generate",
            "output": {
                **formatted_response,
                "provider_used": provider_name,
                "model_used": response.get('model', 'unknown'),
                "raw_response": response if config.get('include_raw', False) else None
            }
        }
    
    async def _process_conversation(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process multi-turn conversation."""
        conversation_id = config.get('conversation_id', 'default')
        user_message = inputs.get('message', inputs.get('prompt', ''))
        
        if not user_message:
            raise ValueError("No message provided for conversation")
        
        # Get or create conversation history
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            
            # Add system prompt if provided
            system_prompt = config.get('system_prompt')
            if system_prompt:
                self.conversations[conversation_id].append({
                    "role": "system", 
                    "content": system_prompt
                })
        
        # Add user message to history
        self.conversations[conversation_id].append({
            "role": "user", 
            "content": user_message
        })
        
        # Manage conversation length
        max_history = config.get('max_history_length', 10)
        if len(self.conversations[conversation_id]) > max_history:
            # Keep system message if present, truncate from beginning
            system_messages = [msg for msg in self.conversations[conversation_id] if msg['role'] == 'system']
            other_messages = [msg for msg in self.conversations[conversation_id] if msg['role'] != 'system']
            
            # Keep last max_history - len(system_messages) messages
            keep_count = max_history - len(system_messages)
            self.conversations[conversation_id] = system_messages + other_messages[-keep_count:]
        
        # Generate response
        provider_name = config.get('provider', 'openai')
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        response = await provider.generate(self.conversations[conversation_id], config)
        
        # Add assistant response to history
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": response.get('content', '')
        })
        
        # Format response
        formatter_name = config.get('response_format', 'detailed')
        formatter = self.formatters.get(formatter_name, self.formatters['detailed'])
        formatted_response = await formatter.format(response, config)
        
        logger.info(f"[GenericLLMProcessor] USCITA conversation (successo): turn {len(self.conversations[conversation_id])//2}")
        return {
            "status": "success",
            "operation": "chat",
            "output": {
                **formatted_response,
                "conversation_id": conversation_id,
                "turn_number": len(self.conversations[conversation_id]) // 2,
                "conversation_length": len(self.conversations[conversation_id])
            }
        }
    
    async def _process_templating(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process prompt templating without generation."""
        template_str = inputs.get('template', config.get('template', ''))
        template_data = inputs.get('data', inputs.get('context', {}))
        
        if not template_str:
            raise ValueError("No template provided")
        
        template_name = config.get('template_engine', 'simple')
        template_engine = self.templates.get(template_name, self.templates['simple'])
        
        formatted_prompt = await template_engine.format(template_str, template_data)
        
        logger.info("[GenericLLMProcessor] USCITA templating (successo): template formatted")
        return {
            "status": "success",
            "operation": "template",
            "output": {
                "formatted_prompt": formatted_prompt,
                "template_engine": template_name,
                "variables_used": list(template_data.keys())
            }
        }
    
    async def _process_formatting(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process response formatting."""
        raw_response = inputs.get('response', inputs.get('llm_response', {}))
        
        if not raw_response:
            raise ValueError("No response provided for formatting")
        
        formatter_name = config.get('formatter', 'detailed')
        formatter = self.formatters.get(formatter_name, self.formatters['detailed'])
        
        formatted_response = await formatter.format(raw_response, config)
        
        logger.info(f"[GenericLLMProcessor] USCITA formatting (successo): {formatter_name} format applied")
        return {
            "status": "success",
            "operation": "format",
            "output": formatted_response
        }
    
    def clear_conversation(self, conversation_id: str = 'default'):
        """Clear conversation history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il Generic LLM Processor."""
    processor = GenericLLMProcessor()
    return await processor.process(context)