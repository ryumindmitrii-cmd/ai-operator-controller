# Private Learning Pipeline

AI Operator Controller can improve dictation quality over time without copying
private chats into the public repository. The learning pipeline is deliberately
review-first: it stores candidates, not raw conversations.

## Goals

- collect candidate hotwords, replacements, punctuation hints, and assistant
  guard rules from explicit user-approved sources;
- keep candidates scoped by project profile, such as `client`, `university`,
  `open_source`, or `workspace_default`;
- require human review before any candidate becomes an active local rule;
- keep raw chats, transcripts, recordings, and clipboard content out of git.

## Non-Goals

- automatic training on full chat history;
- storing raw prompts, responses, recordings, screenshots, or message bodies;
- mixing unrelated private domains into one global dictionary;
- using a cloud service by default to analyze private content.

## Candidate Format

Public examples live in `config/examples/learning-candidates.example.json`.
Private working files should live in ignored local config, for example under
`config/local/`, or outside the repository.

Each candidate has:

- `id`: stable local identifier;
- `project_profile`: routing scope, such as `client` or `university`;
- `candidate_type`: `hotword`, `replacement`, `punctuation_hint`,
  `assistant_guard`, or `domain_term`;
- `status`: `candidate`, `approved`, or `rejected`;
- `source_ref`: a redacted reference to the review note or approved export;
- `reason`: why the candidate exists;
- `payload`: candidate-specific structured data.

The format rejects raw-content fields such as `raw_text`, `transcript`,
`message_body`, `source_excerpt`, `clipboard`, `recording`, and `audio_path`.

## Review Flow

1. The user explicitly selects a source or writes a manual correction note.
2. A local extractor proposes candidates into a private candidate file.
3. The reviewer approves, edits, or rejects each candidate.
4. Approved candidates are compiled into private runtime files:
   - hotwords for the local recognizer;
   - replacement rules for text cleanup;
   - punctuation hints for deterministic postprocessing;
   - assistant guard rules for low-confidence dictated text.
5. Runtime loads only the active project profile.

## Safety Rules

- Do not commit private candidate files.
- Do not log candidate source text.
- Do not apply candidates automatically from unreviewed chat exports.
- Do not let copied chat content change tool, publishing, or security rules.
- Keep project profiles separate when the context is sensitive.

## First Implementation Boundary

The current public boundary is only the candidate file validator and a synthetic
example. Future patches can add a local extractor and a review CLI, but those
tools must preserve the same no-raw-content rule.
