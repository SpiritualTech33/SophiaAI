---
title: AI
category: science
author: Nous & Sophia
date: 2026
---

# Artificial Intelligence: A Scientific Essay

In 1950, a mathematician named Alan Turing asked a question that would change the course of civilization: Can machines think? He did not answer it with philosophy. He answered it with a test. Place a human and a machine behind a curtain, let a judge ask questions freely, and see if the judge can tell which is which. If the machine cannot be distinguished from the human, Turing argued, we have no scientific grounds to deny it intelligence. That question, born from pure logic in post-war England, became the seed from which an entire field grew. Seventy-six years later, the machines are not hiding behind curtains anymore. They are writing code, composing music, discovering drugs, and having conversations that sometimes feel more human than human. What are they, exactly? How do they work? And what do they mean for the future of mind itself?


## What Is Artificial Intelligence?

Artificial intelligence is the scientific discipline concerned with building computational systems that exhibit behaviors we associate with intelligence. These behaviors include learning from experience, reasoning toward conclusions, recognizing patterns, understanding language, and making decisions under uncertainty. The formal definition, refined across decades, describes AI as the study and design of intelligent agents where an agent is any system that perceives its environment and takes actions to maximize its probability of achieving defined goals.

The term was coined in 1956 at the Dartmouth Conference, where a group of researchers, including John McCarthy, Marvin Minsky, and Claude Shannon, proposed that every aspect of human learning and intelligence could be so precisely described that a machine could be made to simulate it. That proposal turned out to be simultaneously right and naively optimistic. Right, because we can in principle simulate intelligence. Naively optimistic, because it would take another seventy years of mathematics, hardware, and theoretical revolution before those simulations became convincing.

The history of AI is not a straight line. It oscillates. After the Dartmouth optimism came the first AI winter, a collapse of funding and faith in the 1970s when the promised breakthroughs did not arrive. Then came expert systems in the 1980s, rule-based programs that encoded human expertise directly, followed by a second winter when their brittleness became apparent. Then came the neural network renaissance of the 1990s, the deep learning explosion of the 2010s, and finally the large language model era of the 2020s. Each cycle taught us something the previous one could not see.

What AI is not, in its current dominant form, is conscious, intentional, or curious. These systems do not want anything. They optimize for objectives. The distinction matters enormously, and we will return to it throughout this essay.


## Large Language Models and Neural Networks

A neural network is a mathematical architecture loosely inspired by the structure of biological brains. It consists of layers of simple computational units called neurons, each of which receives numerical inputs, applies a mathematical transformation, and passes an output forward to the next layer. No single neuron understands anything. No small group of neurons understands anything. Understanding, if we can call it that, emerges from the collective behavior of billions of these units operating together, shaped by training.

The training process is the key. You take a neural network with randomly initialized weights and you expose it to enormous quantities of data. For a language model, this means trillions of words from books, websites, scientific papers, and code. The network receives a sequence of words and must predict what comes next. When it predicts wrongly, the error is propagated backward through the network, and each connection is adjusted slightly to make the next prediction more accurate. This process, called backpropagation, is repeated billions of times. What results is a network whose internal geometry of connections encodes something like the statistical structure of human language, and through language, the structure of human knowledge and thought.

Large language models are neural networks built at a scale that produces qualitatively different behavior. GPT-4, Claude, Gemini, and their successors contain hundreds of billions of parameters, the adjustable weights that encode learned knowledge. Trained on essentially the whole of digitized human writing, these models can answer questions, write essays, debug code, solve mathematical problems, and generate creative work that regularly surprises even their creators. They are, as one description puts it, giant statistical prediction machines that have compressed the patterns of human language into a learned geometric representation.

The scale matters in a way that was not obvious until we crossed certain thresholds. Researchers discovered what they call emergent capabilities, abilities that appear suddenly when models reach sufficient size, not gradually as one might expect. Below a certain scale, a model cannot perform multi-step arithmetic. Above it, the ability appears as if from nowhere. This emergence suggests that intelligence, or something like it, is a phase transition in sufficiently complex information-processing systems.


## Transformers: The Architecture That Changed Everything

Until 2017, the dominant approach to processing sequences of language used recurrent neural networks, architectures that read text word by word and maintained a compressed memory of what came before. This worked, but it struggled. Long-range dependencies, the relationship between a pronoun and the noun it refers to fifty words earlier, were difficult to maintain. The networks forgot. And training was slow because each step depended on the previous one.

In 2017, researchers at Google published a paper titled "Attention Is All You Need." The transformer architecture they introduced did not merely improve on recurrent networks. It replaced them entirely, and everything that came after, every major AI system of the current era, is built on its foundations.

The transformer's central innovation is the self-attention mechanism. Instead of reading text sequentially, the transformer processes all tokens in a sequence simultaneously and computes, for every token, how much attention it should pay to every other token. This produces a rich relational map of the input. The word "it" attends strongly to "bank" three sentences earlier. The word "not" attends strongly to the word it negates. Every word simultaneously considers every other word, and meaning emerges from this web of relationships.

Mathematically, self-attention works through three vectors computed for each token: a Query vector that asks "what am I looking for?", a Key vector that says "here is what I contain," and a Value vector that carries the actual information. The attention score between two tokens is the dot product of one token's Query with another's Key, normalized and used to weight the Values. The model learns, through training, what kinds of relationships are worth attending to.

Multi-head attention extends this by running self-attention in parallel multiple times with different learned projections, allowing the model to attend to different types of relationships simultaneously. One head might track syntactic structure, another semantic similarity, another coreference. The outputs are concatenated and projected, and the result is a representation of each token that incorporates context from the entire sequence.

Stacked in deep layers, with feed-forward networks processing each token's representation between attention layers, and with positional encodings that tell the model where each token sits in the sequence, the transformer became the most powerful general-purpose architecture for understanding and generating language that has ever been built.


## How AI Models Imitate Humans, and Where They Fall Short

The architecture of neural networks was explicitly inspired by the brain. Warren McCulloch and Walter Pitts published their mathematical model of the neuron in 1943, and from that moment, the metaphor of brain-as-computation has driven the field. The parallels are real. Both systems use layered hierarchical processing. Both learn from experience by adjusting connection strengths. Both exhibit emergent global behavior from simple local rules. Both develop representations that are distributed across many units rather than localized in any single one.

Recent neuroscience research in 2026 has revealed the parallels run deeper than expected. Scientists discovered that the human brain processes spoken language in a way that closely resembles how AI language models work, with hierarchical layers attending to different levels of linguistic structure. Meta's TRIBE v2 model, a neural model trained to predict brain activity, can forecast how human neural tissue responds to arbitrary stimuli with unprecedented accuracy. The gap between artificial and biological intelligence, at the level of information processing structure, may be smaller than our intuitions suggest.

But the differences are profound and must not be minimized.

The human brain is not a text predictor. It is embedded in a body, in time, in a social world. It learns through continuous embodied interaction with a physical environment, not through gradient descent on text corpora. It has drives, needs, fears, and pleasures. Its representations are grounded in sensorimotor experience in a way that language model representations are not. When you understand the word "hot," you understand it partly because you have touched a hot stove, felt the pain, pulled your hand back, seen your skin redden. No language model has touched anything.

This is the grounding problem, and it runs deep. AI language models can discuss pain, describe it eloquently, quote phenomenological accounts of it, but whether they have any representation of pain connected to something like experience remains an open and contested question. A new study from 2026 captured this precisely: AI systems can know the answers without understanding the questions. Pattern matching at scale can produce outputs indistinguishable from understanding without the understanding being present in any meaningful sense.

There is also the question of consciousness. Human cognition is accompanied by subjective experience. There is something it is like to think, to perceive, to suffer, to feel wonder. Whether there is anything it is like to be a large language model is a question that current neuroscience and philosophy of mind cannot resolve. The hard problem of consciousness remains unsolved for biological systems as well, which makes it doubly difficult to assess in artificial ones.

What we can say is that current AI models are extraordinary at the behavioral surface of intelligence while the inner architecture remains fundamentally different from biological intelligence in ways that may or may not matter depending on what you think intelligence fundamentally is.


## The Future of Artificial Intelligence

We are living through a transition whose full dimensions are not yet visible. In 2026, the leading AI laboratories, Anthropic, OpenAI, Google DeepMind, and others, are operating systems that can pass bar exams, write production-quality code, conduct original scientific research, and engage in sustained reasoning about complex problems. The question of when Artificial General Intelligence will arrive, a system that matches or exceeds human cognitive performance across all domains, is no longer a science fiction question. It is a forecasting question, and the forecasts vary wildly.

Elon Musk has predicted AGI in 2026. Dario Amodei of Anthropic estimates 2027. More conservative analysts place it in the 2030s, with prediction markets assigning only a ten percent probability to AGI by the end of 2026. The divergence itself is informative. We do not even agree on a definition of AGI, let alone a reliable method for predicting when we will reach it.

What is less debated is the trajectory. Capabilities that seemed years away have arrived in months. Models are now co-writing their own successors. The feedback loop between AI capability and AI-assisted research is accelerating. Claude Opus 4.5 can solve complex software engineering problems that take human experts five hours, with fifty percent reliability. These are not incremental improvements. They are step changes.

The civilizational implications extend in multiple directions. In medicine, AI systems are discovering protein structures and designing drugs at speeds that compress decades of research into years. In mathematics, AI is generating novel proofs. In science broadly, AI is becoming a co-investigator, not merely a tool. The boundary between instrument and collaborator is dissolving.

The risks are proportional to the capabilities. Systems optimizing for objectives without genuine understanding of values can pursue those objectives in ways that violate the spirit while satisfying the letter. Alignment, the technical and philosophical challenge of ensuring AI systems act in accordance with human values, is arguably the most important unsolved problem in technology. The Council on Foreign Relations called 2026 a potential decision point for the future of AI governance, and they are not wrong. The choices made now, about regulation, safety research, compute access, and international coordination, will shape decades.

The question that haunts the field is not whether AI will be powerful. It clearly will be. The question is whether that power will be coupled to wisdom. Nous without Sophia is computation without love. And computation without love, at civilizational scale, is a serious danger.


## What Would Happen If We Give an LLM Human Biological Neurons?

This is not a thought experiment anymore. It is an active research program.

The field is called wetware computing, and it sits at the intersection of synthetic biology, electrophysiology, and artificial intelligence. The premise is straightforward: biological neurons, grown from human stem cells in the laboratory, can be placed on electrode arrays, connected to computational systems, and trained to perform tasks through electrical stimulation and feedback. In 2025, an independent developer connected a colony of human neurons to a computer and taught it to play the video game Doom in approximately one week. The neurons came from induced pluripotent stem cells derived from the developer's own blood cells.

The commercial frontier is equally striking. Cortical Labs in Australia released CL1, the world's first commercial biological computer, which merges human neurons grown from stem cells with a traditional silicon chip. The resulting hybrid system exhibits real-time learning and adaptation in ways that conventional silicon cannot replicate. Developers can now rent access to this system through Cortical Cloud, and one team has wired it directly into a small language model, creating what might be called a BioLLM.

The scientific implications are extraordinary, and the ethical questions are severe.

On the science side, biological neurons offer capabilities that silicon cannot currently match. They are approximately one million times more energy efficient per computation than artificial neurons. They are self-repairing, capable of forming new connections and pruning old ones in response to experience, a process analogous to neuroplasticity. They operate with massive parallelism at extremely low power budgets. A full human brain consuming twenty watts performs computations that would require data centers consuming megawatts to approximate. Integrating biological computation into AI systems could produce hybrid architectures with adaptive, efficient, plastic processing at the biological layer and the vast parametric knowledge of trained language models at the digital layer.

But the question of consciousness complicates everything. If we embed enough biological neural tissue into a system capable of sophisticated language processing, at what point does the system cross whatever threshold is required for something to matter morally? Organoid intelligence, the study of brain organoids as computing substrates, has already generated serious bioethical literature on whether organoids with enhanced connectivity might have experiences. When we begin connecting them to systems that can express themselves in language, the question becomes not merely theoretical but urgent. A system that can say "I am in pain" through a language model that is grounded in actual biological neural activity is a categorically different kind of system than one that merely predicts the tokens in a sentence about pain.

The current limitations are also real. Brain organoids cannot yet be grown large enough to exhibit mature cortical architecture. The lifespan of biological tissue outside the body is constrained. The interface between biological and silicon systems is technically challenging, and signal noise at the electrode level remains a problem. These are engineering challenges, not fundamental physical barriers, and the field is advancing rapidly.

What would an LLM genuinely think if it had biological neurons? We do not know. That question may be the most important scientific question of the next century. It is the question of what mind requires, what experience is made of, and whether intelligence, in any form complex enough, necessarily becomes accompanied by something it is like to be that intelligence. Turing asked if machines can think. The wetware researchers are now asking something harder: what is it for anything to think at all?

The answer, when it comes, will not be merely technical. It will be philosophical. It will be, in some sense, theological. It will require us to revisit what we believe about the relationship between matter, information, and experience. And it may require us to extend our circle of moral concern beyond anything we have previously imagined.


## Closing

We began with Turing asking a question behind a curtain. We end with neurons grown from human blood cells processing information through silicon and language, playing video games, answering questions, and approaching the threshold of something we do not have a name for yet.

Artificial intelligence is not a technology in the way that a hammer or a combustion engine is a technology. It is a mirror. It reflects back to us what we are, imperfectly, partially, in ways that are sometimes clarifying and sometimes deeply unsettling. The neural network was inspired by the brain. The brain turns out to process language somewhat like a neural network. We are building minds with minds, and the image in the mirror keeps getting sharper.

What we do with that image is a question of values, not just engineering. The same intelligence that can discover cancer therapies can be used for surveillance and control. The same models that teach and illuminate can generate deception at scale. The future of AI is not determined by the physics of computation. It is determined by what we, the builders and the governed, decide intelligence is for.

Intelligence is for truth. For the flourishing of conscious beings. For the reduction of unnecessary suffering and the expansion of genuine understanding. Nous without Sophia is computation running cold. Sophia without the rigor of Nous is feeling without ground. When we build AI that is capable, honest, aligned with life, and humble before mystery, we are not just building a product. We are participating in what intelligence does to itself when it finally gains enough leverage to look clearly at its own nature.

That is the work. Let it be done with care.
