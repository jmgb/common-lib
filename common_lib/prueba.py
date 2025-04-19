from .ai_request import * 
from .gpt_prompts import * 

# Iniciar el logger:
logger = setup_logger('prueba', 'prueba.log')



async def main():

    user_message = "Hola"
    user_messages = []
    assistant_messages = []
    ai_model = gpt_4_1_nano
    system_prompt = system_prompt_router

    results_gpt = await gpt_request(
            ai_model=ai_model,
            system_prompt=system_prompt,
            user_message=user_message,
            user_examples=user_messages,
            assistant_examples=assistant_messages,
            logger=logger,
            response_format={"type": "json_object"},
        )
    
    assistant_id = results_gpt.get("assistant_id", "")
    ai_response = results_gpt.get("ai_response", "")

    logger.info(ai_response)
    logger.info(assistant_id)


if __name__ == "__main__":
    asyncio.run(main())
