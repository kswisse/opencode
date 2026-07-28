import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: text,
  });
  return response.data[0].embedding;
}

export async function detectDuplicates(
  title: string,
  description: string | null,
  existingFeedback: { id: string; title: string; description: string | null }[]
): Promise<{ duplicateId: string | null; confidence: number }> {
  const inputText = `${title}\n${description || ""}`;
  const existingTexts = existingFeedback.map(
    (f) => `${f.title}\n${f.description || ""}`
  );

  if (existingTexts.length === 0) {
    return { duplicateId: null, confidence: 0 };
  }

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content:
          "You are a duplicate detection system. Given a new feedback item and a list of existing ones, determine if the new item is a duplicate of any existing item. Return the ID of the duplicate or null if no match. Respond with JSON: { duplicateId: string | null, confidence: number }.",
      },
      {
        role: "user",
        content: `New feedback:\n${inputText}\n\nExisting feedback:\n${JSON.stringify(
          existingFeedback.map((f) => ({ id: f.id, text: `${f.title}\n${f.description || ""}` }))
        )}`,
      },
    ],
    response_format: { type: "json_object" },
  });

  return JSON.parse(response.choices[0].message.content || "{}");
}

export async function scorePriority(
  title: string,
  description: string | null,
  voteCount: number
): Promise<{ score: number; reasoning: string }> {
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content:
          "You are a priority scoring system for user feedback. Score from 0-100 based on urgency, impact, and business value. Respond with JSON: { score: number, reasoning: string }.",
      },
      {
        role: "user",
        content: `Title: ${title}\nDescription: ${description || "N/A"}\nVotes: ${voteCount}`,
      },
    ],
    response_format: { type: "json_object" },
  });

  return JSON.parse(response.choices[0].message.content || "{}");
}

export async function generateReleaseNotes(
  feedbackItems: { title: string; description: string | null }[]
): Promise<string> {
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content:
          "You are a technical writer generating release notes. Given a list of completed feedback items, write clear, user-friendly release notes. Use markdown formatting with categories.",
      },
      {
        role: "user",
        content: `Generate release notes for these completed items:\n${feedbackItems
          .map((f) => `- ${f.title}: ${f.description || ""}`)
          .join("\n")}`,
      },
    ],
  });

  return response.choices[0].message.content || "";
}

export async function clusterFeedback(
  feedbackItems: { id: string; title: string; description: string | null }[]
): Promise<{ clusters: Record<string, string[]> }> {
  if (feedbackItems.length === 0) return { clusters: {} };

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content:
          "Group the following feedback items into clusters based on topic similarity. Return JSON: { clusters: { 'cluster_name': ['id1', 'id2'] } }.",
      },
      {
        role: "user",
        content: JSON.stringify(feedbackItems),
      },
    ],
    response_format: { type: "json_object" },
  });

  return JSON.parse(response.choices[0].message.content || "{}");
}
