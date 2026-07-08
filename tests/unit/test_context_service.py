from app import models
from app.services.context_service import (
    _split_paragraphs,
    build_project_context,
    extract_master_thesis,
    semantic_chunk_text,
)


def test_split_paragraphs_happy_path_with_dense_existential_text():
    text = (
        "Sostengo que la lucidez nace cuando el hombre deja de pedirle absolución al amanecer.\n\n"
        "Defiendo que la culpa no es un accidente moral, sino la arquitectura íntima de nuestra libertad.\n\n"
        "Si cada elección clausura mil futuros, entonces el carácter es la cicatriz visible de aquello que renunciamos a ser."
    )
    paragraphs = _split_paragraphs(text)
    assert paragraphs == [
        "Sostengo que la lucidez nace cuando el hombre deja de pedirle absolución al amanecer.",
        "Defiendo que la culpa no es un accidente moral, sino la arquitectura íntima de nuestra libertad.",
        "Si cada elección clausura mil futuros, entonces el carácter es la cicatriz visible de aquello que renunciamos a ser.",
    ]


def test_build_project_context_constructs_exact_string_with_memory_window_and_rag():
    document_content = (
        "En esta esquina del mundo, la libertad suena a metal cansado.\n\n"
        "La conciencia enumera sus deudas frente al absurdo.\n\n"
        "Sin embargo, insistimos en nombrar sentido donde solo hay intemperie."
    )
    memory = models.EssayMemory(
        thesis="Defiendo que la responsabilidad precede al consuelo.",
        memory_notes="Inicio del texto: En esta esquina del mundo...",
        global_summary="El texto argumenta que la lucidez ética surge del absurdo.",
        summary_status="done",
    )
    rag_chunks = [
        "Fragmento A: la culpa como forma de vigilancia interior.",
        "Fragmento B: la dignidad como disciplina contra la inercia.",
    ]

    context = build_project_context(
        document_content=document_content,
        user_query="Analiza la culpa y la dignidad",
        memory=memory,
        rag_chunks=rag_chunks,
        focus_paragraph_index=1,
        sliding_window_radius=1,
        max_chars=5000,
    )

    expected = (
        "MEMORIA MAESTRA (TESIS):\n"
        "Defiendo que la responsabilidad precede al consuelo.\n\n"
        "SEÑALES DEL DOCUMENTO:\n"
        "Inicio del texto: En esta esquina del mundo...\n\n"
        "RESUMEN GLOBAL JERÁRQUICO:\n"
        "El texto argumenta que la lucidez ética surge del absurdo.\n\n"
        "VENTANA DESLIZANTE DE EDICIÓN (foco en párrafo 1, radio 1):\n"
        "[Párrafo 0]\n"
        "En esta esquina del mundo, la libertad suena a metal cansado.\n\n"
        "[Párrafo 1]\n"
        "La conciencia enumera sus deudas frente al absurdo.\n\n"
        "[Párrafo 2]\n"
        "Sin embargo, insistimos en nombrar sentido donde solo hay intemperie.\n\n"
        "FRAGMENTOS RAG RELEVANTES DEL ENSAYO:\n"
        "[Fragmento 1 de 2]\n"
        "Fragmento A: la culpa como forma de vigilancia interior.\n\n"
        "[Fragmento 2 de 2]\n"
        "Fragmento B: la dignidad como disciplina contra la inercia."
    )
    assert context == expected


def test_semantic_chunk_text_handles_continuous_text_without_newlines():
    continuous_text = (
        "La noche no promete redención. "
        "La ciudad escribe su moral sobre muros húmedos. "
        "Cada rostro parece una versión provisional del miedo. "
        "El hombre elige, y al elegir pierde."
    )
    chunks = semantic_chunk_text(continuous_text, target_chars=80, max_chars=110)
    assert len(chunks) >= 2
    assert all(len(chunk) <= 110 for chunk in chunks)


def test_single_sentence_and_null_empty_special_inputs_do_not_break_context_pipeline():
    one_sentence = "Defiendo que el absurdo no absuelve: obliga."
    assert semantic_chunk_text(one_sentence) == [one_sentence]
    assert extract_master_thesis(one_sentence) == one_sentence

    assert semantic_chunk_text(None) == []
    assert semantic_chunk_text("") == []
    assert extract_master_thesis(None) == ""
    assert extract_master_thesis("") == ""

    special_text = "«¿Quién responde?» —nadie—; solo símbolos: ∴ ∵ § ¶ and 𐍈.\n\nFin."
    special_chunks = semantic_chunk_text(special_text)
    assert len(special_chunks) >= 1
