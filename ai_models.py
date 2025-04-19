# LISTA DE MODELOS DISPONIBLES: 
# Modelos a usar de OpenAI
gpt_4 = "gpt-4o-2024-11-20"
gpt_4_mini ="gpt-4o-mini"   # Nuevo modelo sacado el 18 de Julio de 2024. "gpt-4o-mini-2024-07-18"
gpt_o3_mini = "o3-mini-2025-01-31"  # No tenemos el codigo optimizado para este modelo!
gpt_4_mini_realtime = "gpt-4o-mini-realtime-preview-2024-12-17"
gpt_4_realtime = "gpt-4o-realtime-preview-2024-12-17"
gpt_4_1 = "gpt-4.1-2025-04-14"
gpt_4_1_mini = "gpt-4.1-mini-2025-04-14"
gpt_4_1_nano = "gpt-4.1-nano-2025-04-14"

#Gemini
gemini_flash = "gemini-2.0-flash"
gemini_pro_2_0 = "gemini-2.0-pro-exp-02-05"
gemini_pro_2_5 = 'gemini-2.5-pro-exp-03-25'
gemini_flash_thinking = "gemini-2.0-flash-thinking-exp-01-21"
gemini_image_generation = "gemini-2.0-flash-exp-image-generation"

#Openrouter
gemini_flash_2_0_openrouter = "google/gemini-2.0-flash-001"
gemini_pro_2_5_openrouter_free = "google/gemini-2.5-pro-preview-03-25"
gpt_4_mini_openrouter = "openai/gpt-4o-mini-2024-07-18"     # da errores con pyndatic
gpt_4_openrouter = "openai/gpt-4o-2024-11-20"
claude_sonet_3_7_thinking_openrouter = "anthropic/claude-3.7-sonnet:thinking"
claude_sonet_3_7_openrouter = "anthropic/claude-3.7-sonnet"
deep_seek_r1_openrouter = "deepseek/deepseek-r1"
deep_seek_v3_openrouter_free = "deepseek/deepseek-chat-v3-0324:free"
deep_seek_v3_openrouter = "deepseek/deepseek-chat-v3-0324"

# REPLICATE: MODELOS DE CREACIÓN DE IMÁGENES:
replicate_black_forest_flux_schnell = "black-forest-labs/flux-schnell"
replicate_bytedance_sdxl = "bytedance/sdxl-lightning-4step:5599ed30703defd1d160a25a63321b4dec97101d98b4674bcc56e41f62f35637"
# hidream image model:
replicate_hidream = "prunaai/hidream-l1-fast:2b7cd2858ca8d75aeed6bdb5bf6a1399f54145b7482c857701399a973fcd3dd7"


#Groq Models
# update: https://console.groq.com/docs/models
llama4_scout_groq = "meta-llama/llama-4-scout-17b-16e-instruct"
llama4_maverick_groq = "meta-llama/llama-4-maverick-17b-128e-instruct"

# MODELOS RAZONADORES -> TARDAN EN RESPONDER:
deepseek_r1_llama_groq = "DeepSeek-R1-Distill-Llama-70B"
deepseek_r1_qwen_groq = "DeepSeek-R1-Distill-Qwen-32B"

groq_models = [
    llama4_scout_groq,
    llama4_maverick_groq,
    deepseek_r1_llama_groq,
    deepseek_r1_qwen_groq
]
