# gadget-spec-bot

This bot contains description of mobile phones released. Type in the mobile phone name and see the bot generate the description of the mobile phone.

The intention to create this bot is to capture specifications of all electronic gadgets be it mobile phones, smart watches, Laptops, Tabs, even Blenders. So that its a one stop place to research arrive at your buying decision. Unfortunately I was able to do it only for phones, but can be easily extended to Other Electronic Gadgets.

Detailed documentation of the project can be found in the following URL:

[Project Docs](https://github.com/amogh-kalalbandi/gadget-spec-bot/wiki)


Some points about the project:

1. The project does not contain retrieval evaluation because of the nature of the dataset and the problem I chose to solve.
2. The project does not contain RAG evaluation like how its shown in the LLM Zoomcamp course. Since I am using a derived mistral model (open source one), I was able to verify whether the LLM model was understand the context and generated text or not.
3. The LLM model is not foolproof. There is a lot of hallucinations. 5 out of 10 times it answers the question correctly.
4. Some example prompts of the project:

    - Tell me the specifications of redmi-note-15
    - Tell me the specifications of samsung-galaxy-m35
    - Which is the best phone with 6GB RAM (unpredictable result)
    - Which is the best phone with Snapdragon processor (unpredictable result)
