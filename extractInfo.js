import fs from 'fs';
import { GoogleGenerativeAI } from '@google/genai';

// Load your Gemini API key from environment variables
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

async function run() {
  const text = fs.readFileSync('meeting_notes.txt', 'utf-8');

  const prompt = `
You are an AI assistant that extracts structured information from meeting notes.

From the following text, extract:
- Meeting date
- Location
- Attendees
- Key decisions
- Assigned tasks with deadlines

Respond in JSON format only.

Text:
${text}
  `;
  const model = genAI.getGenerativeModel({ model: 'gemini-pro' });

  const result = await model.generateContentStream({
    contents: [{ role: 'user', parts: [{ text: prompt }] }]
  });

  for await (const chunk of result.stream) {
    process.stdout.write(chunk.text);
  }
}

run().catch(console.error);