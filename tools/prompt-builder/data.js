/* 
  Session Prompt Builder v2 - Registry Initializer
  This file ensures window.promptRegistry exists BEFORE any template scripts load.
*/

window.categories = ['SHIELD', 'Understand', 'Debug', 'Review', 'Refactor', 'Design', 'Planning', 'Build', 'Role', 'Test', 'Handoff', 'Incident'];

// Initialize the global registry array
window.promptRegistry = [];

// Default model suggestions by session category.
// Antigravity is treated as a platform, so the recommendation points to Gemini models commonly used there.
window.modelRecommendations = {
    SHIELD: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Use the quality lane for Product/CTO leadership sessions; use the default lane for worker sessions."
    },
    Understand: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Use the stronger lane when understanding architecture, control flow, or large repo structure."
    },
    Debug: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Use the quality lane for incidents, subtle regressions, or hard root-cause analysis."
    },
    Review: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Use the quality lane when review quality matters more than speed."
    },
    Refactor: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Default lane is enough for most small refactors; use the quality lane for boundary changes."
    },
    Design: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        note: "Architecture and redesign prompts benefit most from the strongest reasoning model."
    },
    Planning: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Use the quality lane for ADRs, roadmaps, and repo-level improvement planning."
    },
    Build: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Default lane is the best balance for feature work, issue fixes, and day-to-day coding."
    },
    Role: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Pick the default lane for most backend/frontend/fullstack/QA sessions."
    },
    Test: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Use the quality lane when designing regression suites or debugging hard flaky tests."
    },
    Handoff: {
        quality: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-nano | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "Handoff and operational summaries usually do not need the strongest model."
    },
    Incident: {
        quality: "OpenAI: gpt-5.4 | Gemini: Gemini 3 Pro | MiniMax: MiniMax-M2.7",
        default: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5",
        budget: "OpenAI: gpt-5.4-mini | Gemini: Gemini 3 Flash | MiniMax: MiniMax-M2.5-highspeed",
        note: "For incidents, prefer the quality lane when the blast radius is meaningful."
    }
};
