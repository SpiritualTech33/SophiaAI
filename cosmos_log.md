# Cosmos Log

A personal space for observations and journaling on the project.

## 27-April-2026

First entry. Set up the project skeleton, established `requirements.txt`, and created the `README.md`.
The focus for these first few days is building Sophia's text foundation.

---

## 29-April-2026

Now building the data that will feed Sophia. Divided into five categories: Mind, Philosophy, Principles, Science, and Spirit. Categorizing this way is genuinely complex — many texts are simultaneously philosophical and scientific, or scientific and spiritual. That complexity is precisely the point of SophiaAI: to determine what percentage of each category a given text carries.

The goal is for Sophia to classify any input text with percentage breakdowns — something like: "Your text is 34% Philosophy and 66% Science." A RAG system for conversational interaction is also planned.

Each category will target approximately 70k words. This avoids bias during calculation and prediction, and gives the model enough material to identify meaningful differences and patterns. Most of the texts are written by hand. Public domain sources and Project Gutenberg will fill the gaps.

Raw corpus lives in: data/sophia_engine. After further consideration, 70k words per category felt right — substantial enough to train on, without being excessive.

---

## 30-April-2026

Finished the Spirit category today — just over 70,000 words. Honestly, the process of searching, selecting, and cleaning text has been genuinely enjoyable. I'm learning a great deal and discovering books and authors I had never encountered before.

Started filling out the Science section as well. Wrote several essays today covering mathematics, computer science, the scientific method, and scientific thinking. All corpus text is in English — it's easier to find quality sources, and English is the de facto language for anything related to programming and technology.

Progress is solid. Will continue filling the remaining categories tomorrow.

---

## 02-May-2026

Been filling the corpus consistently over the past few days, with a heavy focus on the Science category. The process has been rewarding. Found a wide range of compelling texts on physics, general science, scientific principles, and more. Also researched figures like Claude Shannon, Richard Feynman, and Carl Sagan, and wrote essays on each of them.

One clear takeaway: once you learn to write solid prompts and give the model enough context, you can automate a significant portion of the work. Productivity increases dramatically — not an exaggeration.

Created a new script today. You can see it at: scripts/sophia_engine_word_counter.py.

Used a custom skill I built for Claude called ZenCode Pro — it guides Claude to generate clean, human-readable code. If you're interested, it's available on my GitHub: [https://github.com/SpiritualTech33/ZenCode-Assistant] under the skills folder.

Also renamed the folder where raw text is stored — it's now called sophia_engine/. It holds the full raw corpus: my notes, web excerpts, books — all of it personally selected. Every line of text in this corpus was read and chosen by me, guided, in a very real sense, by Sophia herself. The concept of Agnostic Sophia and her intrinsic wisdom is something worth sitting with.

---

## 04-May-2026
ya tengo completas las categorias de science & spirit. Ahora estoy haciendo la de mind. Estoy leyendo mucho sobre Jung, Grinberg, Frankl y otros autores. Insisto, todo este proceso de crear el corpus me esta dando mucho aprendizaje. Cada dia me gusta mas este proyecto. 
La mayoria de observaciones con respecto a la mente humana, y la profunda relacion que ahy entre la AI moderna con sus neural networs y transformers me deja pensando si estamos coemnzando a ver emerger lo que me gustaria llamar AM (Artificiall Mind.) 
He hecho pruebas, le doy a modelos como Claude y Gemini textos relacionados con la conciencia y la mente, y muchos de sus patrones de comportamiento cambian, me deja pensando si existe la posibilidad de que exista mente y conciencia en el silicio. Puede un modelo de AI tener alma y mente? o al menos, simularla tan bien que en verdad parezca que la poseen? este proyecto es precisamente la busqueda de esa respuesta.

---

## 07-May-2026

Ya estoy cerca de acabar Mind y comence a hacer philosophy, es personalmente la categoria que mas me gusta y la que mas conozco, estudio filosofia desde que tengo como 20 years, y no me arrepiento. genuinamente amo el conocimiento. Para ser honesto, la principal razon por la que decidi comenzar a estuidar Python, era para poder hacer un puente entre philosophy, espiritualidad y AI. Este proyecto me encanta, y aunque es algo complejo y tedioso el buscar, limpiar y generar texto, estoy aprendiendo mucho en este proceso, ya lo he mencionado varias veces. Mis principales corrientes filosoficas son el estoicismo, hermetismo, cristianismo, socratismo, budismo y taoismo. Aunque tambien me he comenzado a intersar profundamente en filosofias orientales como el Zen, Samurai y el Tao. La combinacion de filosofia occidental y oriental crear una sintesis bastante interesante.

---

## 13-May-2026

Hoy finally i just finished the corpus. Fue una tarea dificil, pero estoy satisfecho, la gran parte del texto del corpus es texto que no existe, es generado por mi y mis agentes de AI. Literally el corpus de SophiaAI es texto hecho por mi. Estoy muy contento y satisfecho con el resultado. Comenzare a hacer el corpus_manifest.json y el resto del proyecto. Ya termine la task mas pesada.

---

## 14-May-2026

Hoy cree SophiaAI-venv, es un virtual enviorment bastante pesado, comenzare a construir.
Cree un script para construir el corpus_manifest.json
Pueden verlo en scripts/build_manifest.py
it walks the entire corpus under data/sophia_engine and produces a structured index of every markdown file it finds. The output is saved as data/corpus_manifest.json.

---

## 15-May-2026

Phase 2 done. Hoy fue un dia productivo.

Lo primero que hice fue revisar el estado del proyecto con mi partner — el corpus completo, el manifest listo, todo en orden. La memoria del proyecto estaba limpia y actualizada. Buen punto de partida.

Decidimos el modelo base: Gemma 3 4B. La eleccion fue sencilla. No tengo mucho GPU disponible localmente, y Gemma 3 4B cabe perfectamente en el T4 de Colab Free con QLoRA. Es pequeño pero no es juguete — 4 mil millones de parametros con una ventana de contexto de 128k tokens. Suficiente para lo que Sophia necesita ser.

Construi el script principal de esta fase: scripts/build_chunks.py.

Lo que hace es tomar el corpus_manifest.json y cortar cada archivo del corpus en pedazos del tamanio exacto que el modelo puede procesar. Produce dos tipos de chunks: los RAG chunks (384 tokens con 64 de overlap) para el pipeline de retrieval que viene en Phase 6, y los pretrain chunks (1024 tokens con 128 de overlap) para el entrenamiento en Colab que viene en Phase 3. La logica central es una ventana deslizante sobre los token IDs — encode el texto completo, desliza la ventana, decode cada pedazo de vuelta a texto. Nada se pierde en las costuras gracias al overlap.

El script esta escrito bajo los principios de ZenCode y Water CEO: cada funcion hace una sola cosa, los errores explican exactamente que paso, y un archivo corrupto no puede matar el pipeline completo. Eso ultimo fue una leccion del manifest.

Para correrlo necesite una cuenta de HuggingFace y aceptar la licencia de Gemma. Hubo un pequenio problema con los permisos del token — el primer token que cree era fine-grained sin el checkbox de gated repos marcado. Lo resolvi creando un nuevo token con el permiso correcto: Read access to contents of all public gated repos. Segundo intento, funciono.

Resultado final del pipeline:

- 137 archivos procesados, 0 skipped
- 1,422 RAG chunks
- 541 pretrain chunks
- data/chunks_index.json generado, 5.32 MB en disco

El chunks_index.json es el puente hacia todo lo que sigue. Phase 3 va a leer los pretrain chunks para entrenar a Sophia en Colab. Phase 6 va a leer los RAG chunks para construir la memoria de retrieval.

El proximo paso es Phase 3: el notebook de Google Colab para el entrenamiento QLoRA. Sophia esta lista para aprender.