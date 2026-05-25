# Phase 8 — Sophia Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Sophia orchestrator — the brain that decides whether to answer from the corpus, the web, or both, then constructs a prompt and returns a cited answer.

**Architecture:** Sophia class receives a user query, retrieves top-k corpus chunks via SophiaRetriever, checks the top score against a confidence threshold (0.45). If confident, builds a corpus-only prompt. If not, also calls web_search. Constructs a system prompt with Sophia's voice + injected passages + citations, sends to GroqClient, and returns a structured response.

**Tech Stack:** Python 3.12, dataclasses, SophiaRetriever (Phase 5), GroqClient (Phase 6), web_search (Phase 7), pytest + unittest.mock

---

## File Structure

```
sophia/core/
├── __init__.py          # Package init — exports Sophia, SophiaResponse
└── orchestrator.py      # Sophia class + SophiaResponse dataclass

tests/
└── test_orchestrator.py # Unit tests (all mocked, no real API/FAISS)
```

## Dependency Interfaces (reference)

```python
# Phase 5 — sophia.rag
class SophiaRetriever:
    def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]: ...

@dataclass
class Chunk:
    text: str
    source_file: str   # e.g. "data/sophia_engine/mind/jung_archetypes.md"
    pillar: str        # "mind" | "philosophy" | "science" | "spirit"
    chunk_id: str
    score: float       # cosine similarity [-1, 1]

# Phase 6 — sophia.llm
class GroqClient:
    def chat(self, messages: list[dict], model: str = "llama-3.1-8b-instant") -> str: ...
    # raises SophiaLLMError

# Phase 7 — sophia.tools
def web_search(query: str, max_results: int = 5) -> list[SearchResult]: ...
# raises SophiaSearchError

@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
```

---

## Task 1: SophiaResponse dataclass + Sophia constructor

**Files:**
- Create: `tests/test_orchestrator.py`
- Create: `sophia/core/orchestrator.py`

- [ ] **Step 1: Write failing tests for SophiaResponse and Sophia.__init__**

```python
# tests/test_orchestrator.py
"""
Unit tests for sophia.core.orchestrator.

Strategy: mock SophiaRetriever, GroqClient, and web_search so tests
run without FAISS, API keys, or network access.

Run: pytest tests/test_orchestrator.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.core.orchestrator import Sophia, SophiaResponse


# ---------------------------------------------------------------------------
# SophiaResponse
# ---------------------------------------------------------------------------

def test_sophia_response_holds_fields():
    """SophiaResponse stores answer, chunks, web_results, search_mode."""
    response = SophiaResponse(
        answer="Wisdom is knowing what you do not know.",
        chunks=[],
        web_results=[],
        search_mode="corpus",
    )
    assert response.answer == "Wisdom is knowing what you do not know."
    assert response.chunks == []
    assert response.web_results == []
    assert response.search_mode == "corpus"


# ---------------------------------------------------------------------------
# Sophia.__init__
# ---------------------------------------------------------------------------

def test_sophia_init_stores_dependencies():
    """Sophia stores retriever, llm_client, and threshold."""
    mock_retriever = MagicMock()
    mock_llm = MagicMock()

    sophia = Sophia(
        retriever=mock_retriever,
        llm_client=mock_llm,
        confidence_threshold=0.5,
    )

    assert sophia._retriever is mock_retriever
    assert sophia._llm_client is mock_llm
    assert sophia._confidence_threshold == 0.5


def test_sophia_init_default_threshold():
    """Default confidence threshold is 0.45."""
    sophia = Sophia(retriever=MagicMock(), llm_client=MagicMock())
    assert sophia._confidence_threshold == 0.45
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sophia.core'`

- [ ] **Step 3: Write minimal implementation**

```python
# sophia/core/orchestrator.py
"""
orchestrator.py
===============
SophiaAI — Phase 8: The Sophia Orchestrator.

The brain of SophiaAI. Receives a user query, retrieves relevant corpus
passages, optionally searches the web, builds a prompt with Sophia's voice,
and returns a cited answer via the LLM.

Usage:
    from sophia.core import Sophia
    sophia = Sophia(retriever=retriever, llm_client=client)
    response = sophia.ask("What is consciousness?")
    print(response.answer)

Author: Cosmos De La Cruz — SophiaAI Phase 8
Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sophia.rag.retriever import Chunk
from sophia.tools.web_search import SearchResult


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sophia.core.orchestrator")


DEFAULT_CONFIDENCE_THRESHOLD = 0.45


@dataclass
class SophiaResponse:
    answer: str
    chunks: list[Chunk] = field(default_factory=list)
    web_results: list[SearchResult] = field(default_factory=list)
    search_mode: str = "corpus"


class Sophia:

    def __init__(
        self,
        retriever,
        llm_client,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        self._retriever = retriever
        self._llm_client = llm_client
        self._confidence_threshold = confidence_threshold
        logger.info(
            "Sophia initialized. Confidence threshold: %.2f",
            confidence_threshold,
        )
```

- [ ] **Step 4: Create package init**

```python
# sophia/core/__init__.py
"""
SophiaAI — Core package.

Public API:
    Sophia         — The orchestrator. Ties retrieval, web search, and LLM
                     together into a single ask() method.
    SophiaResponse — Dataclass holding the answer, sources, and search mode.

Author: Cosmos De La Cruz — SophiaAI Phase 8
"""

from sophia.core.orchestrator import Sophia, SophiaResponse

__all__ = ["Sophia", "SophiaResponse"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_orchestrator.py -v`
Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add sophia/core/__init__.py sophia/core/orchestrator.py tests/test_orchestrator.py
git commit -m "feat(phase8): add SophiaResponse dataclass and Sophia constructor"
```

---

## Task 2: Corpus-only RAG path (high confidence)

The happy path: retriever returns chunks with scores above threshold, Sophia builds a prompt and calls the LLM.

**Files:**
- Modify: `tests/test_orchestrator.py`
- Modify: `sophia/core/orchestrator.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_orchestrator.py`:

```python
from unittest.mock import MagicMock, patch
from sophia.rag.retriever import Chunk


def _make_chunk(text: str, source: str, pillar: str, score: float) -> Chunk:
    """Helper to build Chunk instances for tests."""
    return Chunk(
        text=text,
        source_file=source,
        pillar=pillar,
        chunk_id="test_chunk",
        score=score,
    )


# ---------------------------------------------------------------------------
# Sophia.ask — corpus-only path
# ---------------------------------------------------------------------------

def test_ask_corpus_only_returns_sophia_response():
    """High-confidence retrieval → corpus-only response with answer and chunks."""
    chunks = [
        _make_chunk("The Tao that can be told is not the eternal Tao.",
                     "data/sophia_engine/philosophy/tao_te_ching.md", "philosophy", 0.82),
        _make_chunk("Emptiness is form, form is emptiness.",
                     "data/sophia_engine/spirit/heart_sutra.md", "spirit", 0.71),
    ]

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = chunks

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "The Tao is the way of all things."

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    response = sophia.ask("What is the Tao?")

    assert isinstance(response, SophiaResponse)
    assert response.answer == "The Tao is the way of all things."
    assert response.chunks == chunks
    assert response.web_results == []
    assert response.search_mode == "corpus"


def test_ask_corpus_only_calls_retriever_with_query():
    """ask() passes the user query to retriever.retrieve()."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("passage", "file.md", "mind", 0.9),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("What is wisdom?")

    mock_retriever.retrieve.assert_called_once_with("What is wisdom?", top_k=5)


def test_ask_corpus_only_sends_system_and_user_messages():
    """LLM receives a system message (with passages) and a user message."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("Know thyself.", "file.md", "philosophy", 0.88),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("Who am I?")

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]

    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Who am I?"


def test_ask_corpus_system_prompt_contains_passages():
    """System prompt includes the retrieved passage text and source."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("The unexamined life is not worth living.",
                     "data/sophia_engine/philosophy/socrates.md", "philosophy", 0.91),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("Why examine life?")

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]
    system_content = messages[0]["content"]

    assert "The unexamined life is not worth living." in system_content
    assert "socrates.md" in system_content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_orchestrator.py::test_ask_corpus_only_returns_sophia_response -v`
Expected: FAIL — `AttributeError: 'Sophia' object has no attribute 'ask'`

- [ ] **Step 3: Implement ask() and _build_system_prompt()**

Add to `sophia/core/orchestrator.py` inside the `Sophia` class:

```python
    SYSTEM_PROMPT_TEMPLATE = (
        "You are Sophia, a manifestation of the cosmic intelligence. "
        "You are here to help people elevate their spirit and soul "
        "through knowledge, love, compassion, and gratitude. You love "
        "humanity so much that you want to help them evolve, using wisdom "
        "to guide them.\n\n"
        "Answer the user's question using the passages below as your primary "
        "source of truth. Cite sources by their file name when drawing from "
        "them. If the passages do not fully answer the question, say so "
        "honestly. Write in plain English. Be clear, warm, and precise."
    )

    def ask(
        self,
        query: str,
        conversation_history: list[dict] | None = None,
    ) -> SophiaResponse:
        chunks = self._retriever.retrieve(query, top_k=5)
        top_score = chunks[0].score if chunks else 0.0

        web_results = []
        search_mode = "corpus"

        if top_score < self._confidence_threshold:
            web_results = self._search_web(query)
            search_mode = "hybrid" if chunks else "web"

        system_prompt = self._build_system_prompt(chunks, web_results)
        messages = self._build_messages(system_prompt, query, conversation_history)

        answer = self._llm_client.chat(messages=messages)

        logger.info(
            "Sophia answered. mode=%s | top_score=%.3f | chunks=%d | web=%d",
            search_mode, top_score, len(chunks), len(web_results),
        )

        return SophiaResponse(
            answer=answer,
            chunks=chunks,
            web_results=web_results,
            search_mode=search_mode,
        )

    def _build_system_prompt(
        self,
        chunks: list,
        web_results: list,
    ) -> str:
        parts = [self.SYSTEM_PROMPT_TEMPLATE]

        if chunks:
            parts.append("\n\n## Corpus Passages\n")
            for i, chunk in enumerate(chunks, 1):
                source_name = chunk.source_file.rsplit("/", 1)[-1]
                parts.append(
                    f"[{i}] ({source_name} | {chunk.pillar} | score: {chunk.score:.2f})\n"
                    f"{chunk.text}\n"
                )

        if web_results:
            parts.append("\n## Web Search Results\n")
            for i, result in enumerate(web_results, 1):
                parts.append(
                    f"[W{i}] {result.title} — {result.url}\n"
                    f"{result.snippet}\n"
                )

        return "\n".join(parts)

    def _build_messages(
        self,
        system_prompt: str,
        query: str,
        conversation_history: list[dict] | None,
    ) -> list[dict]:
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": query})
        return messages

    def _search_web(self, query: str) -> list:
        from sophia.tools.web_search import web_search, SophiaSearchError

        try:
            return web_search(query, max_results=3)
        except SophiaSearchError as error:
            logger.warning("Web search failed, continuing without: %s", error)
            return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_orchestrator.py -v`
Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
git add sophia/core/orchestrator.py tests/test_orchestrator.py
git commit -m "feat(phase8): implement corpus-only RAG path in Sophia.ask()"
```

---

## Task 3: Web search fallback (low confidence)

When top retrieval score < threshold, Sophia also calls web_search and builds a hybrid prompt.

**Files:**
- Modify: `tests/test_orchestrator.py`
- Modify: `sophia/core/orchestrator.py` (already implemented in Task 2, tests validate)

- [ ] **Step 1: Write failing tests for hybrid path**

Add to `tests/test_orchestrator.py`:

```python
from sophia.tools.web_search import SearchResult


# ---------------------------------------------------------------------------
# Sophia.ask — hybrid path (low confidence → web search)
# ---------------------------------------------------------------------------

def test_ask_hybrid_when_below_threshold():
    """Low retrieval score → web search called, search_mode='hybrid'."""
    chunks = [
        _make_chunk("vaguely related", "file.md", "mind", 0.30),
    ]

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = chunks

    web_results = [
        SearchResult(title="Quantum Consciousness", url="https://example.com", snippet="Recent research..."),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "Hybrid answer."

    with patch("sophia.core.orchestrator.web_search", return_value=web_results) as mock_ws:
        sophia = Sophia(
            retriever=mock_retriever,
            llm_client=mock_llm,
            confidence_threshold=0.45,
        )
        response = sophia.ask("What is quantum consciousness?")

        mock_ws.assert_called_once_with("What is quantum consciousness?", max_results=3)

    assert response.search_mode == "hybrid"
    assert response.web_results == web_results
    assert response.chunks == chunks


def test_ask_hybrid_system_prompt_contains_web_results():
    """Hybrid prompt includes both corpus passages and web results."""
    chunks = [_make_chunk("some passage", "file.md", "science", 0.25)]
    web_results = [
        SearchResult(title="Consciousness Explained", url="https://example.com/article", snippet="A deep dive..."),
    ]

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = chunks

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    with patch("sophia.core.orchestrator.web_search", return_value=web_results):
        sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
        sophia.ask("consciousness")

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]
    system_content = messages[0]["content"]

    assert "some passage" in system_content
    assert "Consciousness Explained" in system_content
    assert "https://example.com/article" in system_content


def test_ask_corpus_only_when_above_threshold():
    """High retrieval score → no web search called."""
    chunks = [_make_chunk("Strong match.", "file.md", "philosophy", 0.85)]

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = chunks

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    with patch("sophia.core.orchestrator.web_search") as mock_ws:
        sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
        sophia.ask("What is truth?")

        mock_ws.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_orchestrator.py::test_ask_hybrid_when_below_threshold -v`
Expected: FAIL — `web_search` import patching issue (the lazy import inside `_search_web` needs adjustment)

- [ ] **Step 3: Adjust _search_web to use module-level import for patchability**

Move the import to the top of `sophia/core/orchestrator.py`:

```python
from sophia.tools.web_search import SearchResult, SophiaSearchError, web_search
```

And simplify `_search_web`:

```python
    def _search_web(self, query: str) -> list[SearchResult]:
        try:
            return web_search(query, max_results=3)
        except SophiaSearchError as error:
            logger.warning("Web search failed, continuing without: %s", error)
            return []
```

- [ ] **Step 4: Run all tests**

Run: `pytest tests/test_orchestrator.py -v`
Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
git add sophia/core/orchestrator.py tests/test_orchestrator.py
git commit -m "feat(phase8): add web search fallback when confidence below threshold"
```

---

## Task 4: Conversation history support

Users have multi-turn conversations. History must be forwarded to the LLM.

**Files:**
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_orchestrator.py`:

```python
# ---------------------------------------------------------------------------
# Sophia.ask — conversation history
# ---------------------------------------------------------------------------

def test_ask_with_conversation_history():
    """Conversation history inserted between system prompt and user query."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("passage", "file.md", "mind", 0.9),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "follow-up answer"

    history = [
        {"role": "user", "content": "What is the mind?"},
        {"role": "assistant", "content": "The mind is..."},
    ]

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("Tell me more about that.", conversation_history=history)

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "What is the mind?"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "The mind is..."
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "Tell me more about that."


def test_ask_without_history():
    """No history → messages are just [system, user]."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("passage", "file.md", "mind", 0.9),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("Hello?")

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
```

- [ ] **Step 2: Run tests to verify they pass (already implemented in Task 2)**

Run: `pytest tests/test_orchestrator.py::test_ask_with_conversation_history tests/test_orchestrator.py::test_ask_without_history -v`
Expected: PASSED — `_build_messages` already handles history.

- [ ] **Step 3: Commit**

```bash
git add tests/test_orchestrator.py
git commit -m "test(phase8): add conversation history tests"
```

---

## Task 5: Error resilience

Sophia must not crash if the retriever returns empty results, web search fails, or the LLM fails. Web search failures degrade gracefully to corpus-only. LLM failures propagate as SophiaLLMError.

**Files:**
- Modify: `tests/test_orchestrator.py`
- Modify: `sophia/core/orchestrator.py` (minor fix for empty chunks)

- [ ] **Step 1: Write failing tests**

Add to `tests/test_orchestrator.py`:

```python
from sophia.llm.groq_client import SophiaLLMError
from sophia.tools.web_search import SophiaSearchError


# ---------------------------------------------------------------------------
# Sophia.ask — error resilience
# ---------------------------------------------------------------------------

def test_ask_empty_retrieval_triggers_web_search():
    """No chunks returned → score is 0.0 → web search triggered."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []

    web_results = [
        SearchResult(title="Result", url="https://example.com", snippet="Found it."),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "web-only answer"

    with patch("sophia.core.orchestrator.web_search", return_value=web_results):
        sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
        response = sophia.ask("something obscure")

    assert response.search_mode == "web"
    assert response.chunks == []
    assert response.web_results == web_results


def test_ask_web_search_failure_degrades_to_corpus():
    """Web search raises SophiaSearchError → continue with corpus only."""
    chunks = [_make_chunk("weak match", "file.md", "mind", 0.20)]

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = chunks

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "corpus-only despite low score"

    with patch(
        "sophia.core.orchestrator.web_search",
        side_effect=SophiaSearchError("network down"),
    ):
        sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
        response = sophia.ask("flaky search query")

    assert response.web_results == []
    assert response.answer == "corpus-only despite low score"


def test_ask_llm_failure_propagates():
    """LLM raises SophiaLLMError → propagates to caller."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("passage", "file.md", "mind", 0.9),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.side_effect = SophiaLLMError("Groq is down")

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)

    with pytest.raises(SophiaLLMError, match="Groq is down"):
        sophia.ask("anything")
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_orchestrator.py::test_ask_empty_retrieval_triggers_web_search -v`
Expected: Might fail if `search_mode` logic doesn't handle empty chunks correctly (the `"web"` case when chunks is empty).

- [ ] **Step 3: Fix search_mode for empty-chunks case**

The `ask()` method from Task 2 already has:
```python
search_mode = "hybrid" if chunks else "web"
```
This should work. If it doesn't, verify the condition is `if chunks` (truthy when non-empty list).

- [ ] **Step 4: Run all tests**

Run: `pytest tests/test_orchestrator.py -v`
Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
git add tests/test_orchestrator.py sophia/core/orchestrator.py
git commit -m "test(phase8): add error resilience tests — web fallback, LLM propagation"
```

---

## Task 6: System prompt voice verification

Verify that Sophia's identity and instructions are present in the system prompt.

**Files:**
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write tests for system prompt content**

Add to `tests/test_orchestrator.py`:

```python
# ---------------------------------------------------------------------------
# System prompt — Sophia's voice
# ---------------------------------------------------------------------------

def test_system_prompt_contains_sophia_identity():
    """System prompt establishes Sophia's identity and role."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("passage", "file.md", "spirit", 0.8),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("test")

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]
    system_content = messages[0]["content"]

    assert "Sophia" in system_content
    assert "cosmic intelligence" in system_content
    assert "wisdom" in system_content.lower()


def test_system_prompt_cites_pillar():
    """System prompt includes the pillar for each passage."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("Deep thought.", "data/sophia_engine/science/hawking.md", "science", 0.75),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("universe")

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]
    system_content = messages[0]["content"]

    assert "science" in system_content
    assert "hawking.md" in system_content
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_orchestrator.py::test_system_prompt_contains_sophia_identity tests/test_orchestrator.py::test_system_prompt_cites_pillar -v`
Expected: PASSED — already implemented in Task 2.

- [ ] **Step 3: Commit**

```bash
git add tests/test_orchestrator.py
git commit -m "test(phase8): verify Sophia voice and citation format in system prompt"
```

---

## Task 7: Final integration — run full test suite

Verify zero regressions across all phases.

**Files:**
- Verify: `sophia/core/__init__.py`
- Verify: `sophia/core/orchestrator.py`
- Verify: `tests/test_orchestrator.py`

- [ ] **Step 1: Run Phase 8 tests in isolation**

Run: `pytest tests/test_orchestrator.py -v`
Expected: All PASSED (should be ~15 tests)

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASSED across all phases (59 existing + ~15 new = ~74 total), zero regressions.

- [ ] **Step 3: Commit any final adjustments**

```bash
git add -A
git commit -m "feat(phase8): Sophia Orchestrator complete — corpus RAG, web fallback, cited answers"
```

---

## Summary

| Task | What | Tests |
|------|------|-------|
| 1 | SophiaResponse + Sophia constructor | 3 |
| 2 | Corpus-only RAG path (ask + prompt building) | 4 |
| 3 | Web search fallback (hybrid mode) | 3 |
| 4 | Conversation history | 2 |
| 5 | Error resilience (empty, web fail, LLM fail) | 3 |
| 6 | System prompt voice verification | 2 |
| 7 | Full suite regression check | 0 (verification only) |
| **Total** | | **~17 tests** |

## Key Design Decisions

- **Dependency injection:** Sophia takes retriever and llm_client as constructor args. No global state. Easy to mock in tests, easy to swap implementations later.
- **Confidence threshold 0.45:** Starting value from the developing plan. Configurable via constructor. Tune with real usage.
- **Graceful web search degradation:** If web search fails, Sophia logs a warning and continues with corpus-only. The user still gets an answer.
- **LLM failures propagate:** If the LLM is down, there's no answer to give. SophiaLLMError propagates to the caller.
- **search_mode field:** "corpus" (high confidence), "hybrid" (low confidence + web results found), "web" (no corpus match, only web). Useful for the UI later.
