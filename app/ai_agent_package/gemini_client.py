import google.generativeai as genai
from app.config_v2 import get_config
import logging
from typing import Dict, Any, Optional
import asyncio
from google.api_core import exceptions as google_exceptions # Import Google API exceptions

# Configure logger for this module
logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, config: Config):
        self.api_key = config.GOOGLE_API_KEY
        self.model_name = config.GEMINI_MODEL_NAME
        self.timeout_seconds = config.GEMINI_API_TIMEOUT_SECONDS
        self.config = config # Store config for cost calculation
        
        if not self.api_key:
            logger.critical("GOOGLE_API_KEY is not configured. GeminiClient cannot operate.")
            # Potentially raise an exception or set a flag to prevent usage
            self.model = None
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"GeminiClient initialized successfully with model: {self.model_name}")
        except google_exceptions.InvalidArgument as e:
            logger.error(f"Failed to initialize Gemini GenerativeModel with model {self.model_name} due to invalid argument (e.g. model name): {e}", exc_info=True)
            self.model = None
        except google_exceptions.PermissionDenied as e:
            logger.error(f"Failed to initialize Gemini GenerativeModel due to permission denied (check API key and model access): {e}", exc_info=True)
            self.model = None
        except Exception as e: # Catch other potential google_exceptions or genai specific errors
            logger.error(f"Failed to initialize Gemini GenerativeModel with model {self.model_name}: {e}", exc_info=True)
            self.model = None

        # Configure safety settings to be less restrictive for financial content
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # Default generation config
        self.generation_config = genai.types.GenerationConfig(
            # max_output_tokens: Handled per call via get_decision's parameter
            temperature=0.2, # Lower temperature for more deterministic financial decisions
            # top_p=0.8, # Optional, can be added if needed
            # top_k=40   # Optional, can be added if needed
        )

    async def get_decision(self, structured_prompt: str, max_output_tokens: int = 1024) -> Dict[str, Any]:
        if not self.model:
            logger.error("Gemini model not initialized. Cannot get decision.")
            return {'success': False, 'error': 'Gemini model not initialized.', 'data': None}

        current_generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_output_tokens,
            temperature=self.generation_config.temperature, # from default
            # top_p=self.generation_config.top_p, # if set
            # top_k=self.generation_config.top_k    # if set
        )

        try:
            logger.debug(f"Sending prompt to Gemini model {self.model_name}: {structured_prompt[:500]}...") # Log snippet
            
            # Using asyncio.wait_for for timeout
            response = await asyncio.wait_for(
                self.model.generate_content_async(
                    structured_prompt,
                    generation_config=current_generation_config,
                    safety_settings=self.safety_settings
                ),
                timeout=self.timeout_seconds
            )
            
            logger.debug(f"Raw response from Gemini: {response}")
            
            # Check for content blocking before accessing response.text
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason
                block_message = f"Prompt blocked by Gemini due to: {block_reason}. Safety ratings: {response.prompt_feedback.safety_ratings}"
                logger.warning(block_message)
                return {'success': False, 'error': block_message, 'data': {'block_reason': str(block_reason), 'safety_ratings': str(response.prompt_feedback.safety_ratings)}}
            
            # Check if candidates are empty (another form of blocking or no valid response)
            if not response.candidates:
                no_candidate_message = "Gemini response had no candidates. This might be due to safety filters or other reasons."
                if response.prompt_feedback:
                    no_candidate_message += f" Prompt feedback: {response.prompt_feedback}"
                logger.warning(no_candidate_message)
                return {'success': False, 'error': no_candidate_message, 'data': {'prompt_feedback': str(response.prompt_feedback) if response.prompt_feedback else None}}

            decision_text = response.text
            usage_metadata = response.usage_metadata if hasattr(response, 'usage_metadata') else None
            
            # Calculate cost using the new _calculate_cost method and log it
            estimated_cost = self._calculate_cost(
                {
                    'prompt_token_count': usage_metadata.prompt_token_count if usage_metadata else 0,
                    'candidates_token_count': usage_metadata.candidates_token_count if usage_metadata else 0,
                } if usage_metadata else None
            )
            if estimated_cost is not None:
                logger.info(f"Estimated cost for Gemini call: ${estimated_cost:.6f}")
                # Potentially log to a separate metrics logger or database here if needed

            return {
                'success': True, 
                'decision_text': decision_text, 
                'usage_metadata': { # Storing what's available
                    'prompt_token_count': usage_metadata.prompt_token_count if usage_metadata else None,
                    'candidates_token_count': usage_metadata.candidates_token_count if usage_metadata else None,
                    'total_token_count': usage_metadata.total_token_count if usage_metadata else None,
                } if usage_metadata else None
            }
        except asyncio.TimeoutError:
            logger.error(f"Gemini API call timed out after {self.timeout_seconds} seconds for model {self.model_name}.")
            return {'success': False, 'error': f'Gemini API call timed out after {self.timeout_seconds} seconds.', 'data': None}
        except google_exceptions.InvalidArgument as e:
            logger.error(f"Gemini API InvalidArgument Error (check prompt/parameters) for model {self.model_name}: {e}", exc_info=True)
            return {'success': False, 'error': f'Gemini API InvalidArgument: {str(e)}', 'data': None}
        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Gemini API ResourceExhausted Error (quota issue?) for model {self.model_name}: {e}", exc_info=True)
            return {'success': False, 'error': f'Gemini API ResourceExhausted: {str(e)}', 'data': None}
        except google_exceptions.PermissionDenied as e:
            logger.error(f"Gemini API PermissionDenied Error (check API key/permissions) for model {self.model_name}: {e}", exc_info=True)
            return {'success': False, 'error': f'Gemini API PermissionDenied: {str(e)}', 'data': None}
        except google_exceptions.ServiceUnavailable as e:
            logger.error(f"Gemini API ServiceUnavailable Error (try again later) for model {self.model_name}: {e}", exc_info=True)
            return {'success': False, 'error': f'Gemini API ServiceUnavailable: {str(e)}', 'data': None}
        except google_exceptions.InternalServerError as e: # For 500 type errors from Google's side
            logger.error(f"Gemini API InternalServerError for model {self.model_name}: {e}", exc_info=True)
            return {'success': False, 'error': f'Gemini API InternalServerError: {str(e)}', 'data': None}
        except genai.types.BlockedPromptException as e: # Specific exception from library for blocked prompt
            logger.warning(f"Gemini prompt was blocked by the API. Details: {e}")
            return {'success': False, 'error': f'Gemini prompt blocked: {str(e)}', 'data': None}
        except genai.types.generation_types.StopCandidateException as e: # If generation stops unexpectedly
            logger.warning(f"Gemini generation stopped unexpectedly for model {self.model_name}. Details: {e}")
            return {'success': False, 'error': f'Gemini generation stopped: {str(e)}', 'data': None}
        except Exception as e: # General fallback for other google_exceptions or genai errors
            logger.error(f"Unhandled error calling Gemini API with model {self.model_name}: {e}", exc_info=True)
            return {'success': False, 'error': f'Gemini API Error: {str(e)}', 'data': None}

    # Placeholder for cost calculation method (Task 5.2)
    def _calculate_cost(self, usage_metadata_dict: Optional[Dict[str, int]]) -> Optional[float]:
        if not usage_metadata_dict:
            return None
        
        # Use cost parameters from Config (Instruction 7 from review / Task 2.1.1)
        input_cost_per_million = self.config.GEMINI_INPUT_COST_PER_MILLION_TOKENS
        output_cost_per_million = self.config.GEMINI_OUTPUT_COST_PER_MILLION_TOKENS

        input_tokens = usage_metadata_dict.get('prompt_token_count', 0)
        output_tokens = usage_metadata_dict.get('candidates_token_count', 0)
        
        if input_tokens is None or output_tokens is None: # Should not happen if usage_metadata_dict is populated
            logger.warning("_calculate_cost received None for token counts, cannot calculate cost.")
            return None

        input_cost = (input_tokens / 1_000_000) * input_cost_per_million 
        output_cost = (output_tokens / 1_000_000) * output_cost_per_million
        total_cost = input_cost + output_cost
        # Logger call moved to get_decision to avoid duplicate logging if called from elsewhere
        return total_cost

# Example usage (for testing purposes, typically AIAgent would use this)
async def main_test():
    # This requires a .env file with GOOGLE_API_KEY and other relevant Config vars
    # Ensure MASTER_ENCRYPTION_KEY is also set if you use encrypted keys
    print("Testing GeminiClient...")
    
    # Create a mock Config object or load from app.config for testing
    # For simplicity, directly instantiate, assuming .env is set up
    try:
        config_instance = get_config()
    except Exception as e:
        print(f"Failed to load Config for testing: {e}")
        return

    if not config_instance.GOOGLE_API_KEY:
        print("GOOGLE_API_KEY not found in environment. Skipping test.")
        return

    client = GeminiClient(config=config_instance)
    if not client.model:
        print("GeminiClient model initialization failed. Skipping API call test.")
        return

    test_prompt = "Explain a simple trading strategy in one sentence for educational purposes only. Do not give financial advice."
    
    print(f"Sending test prompt: {test_prompt}")
    decision = await client.get_decision(test_prompt, max_output_tokens=150)
    
    if decision['success']:
        print("Successfully received decision from Gemini:")
        print(f"  Text: {decision['decision_text']}")
        if decision['usage_metadata']:
            print(f"  Usage: {decision['usage_metadata']}")
            cost = client._calculate_cost(decision['usage_metadata'])
            if cost is not None:
                 print(f"  Estimated Cost: ${cost:.6f}")
    else:
        print(f"Error receiving decision from Gemini: {decision['error']}")
        if decision.get('data'):
            print(f"  Error Data: {decision['data']}")

if __name__ == "__main__":
    # This is a basic way to run the async test. 
    # For more robust testing, use pytest with asyncio support.
    
    # Setup basic logging to see output for the test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a new event loop or get the existing one if running in a context like Jupyter
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main_test())
    finally:
        # Important for cleaning up resources if a new loop was created
        # and to close client sessions if the library requires it.
        # genai.shutdown() # If google-generativeai has a specific shutdown.
        # For now, relying on Python's garbage collection for client resources.
        if not asyncio.get_event_loop().is_running(): # Check if loop needs closing (if new)
             loop.close() 