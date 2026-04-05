"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { importCandidate } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function ImportCandidatePage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;

  const [listingText, setListingText] = useState("");
  const [chatText, setChatText] = useState("");
  const [noteText, setNoteText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!listingText.trim() && !chatText.trim() && !noteText.trim()) {
      setError("Please paste at least one source of text.");
      return;
    }

    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    setLoading(true);
    try {
      await importCandidate(token, projectId, {
        source_type: listingText && chatText ? "mixed" : listingText ? "manual_text" : "chat_log",
        raw_listing_text: listingText || undefined,
        raw_chat_text: chatText || undefined,
        raw_note_text: noteText || undefined,
      });
      router.push(`/projects/${projectId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to import candidate.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <Link
          href={`/projects/${projectId}`}
          className="text-sm text-gray-500 hover:text-gray-700 mb-4 inline-block"
        >
          Back to project
        </Link>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Add a candidate</h1>
        <p className="text-gray-600 mb-6">
          Paste the listing text, agent chat, or your own notes. RentWise will extract the key details and
          decide what to verify next.
        </p>

        {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}

        <form onSubmit={handleImport} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Listing text</label>
            <textarea
              value={listingText}
              onChange={(e) => setListingText(e.target.value)}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Paste the property ad or listing details here..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Agent or landlord chat (optional)</label>
            <textarea
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Paste the conversation if it contains extra pricing or clause details..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Your notes (optional)</label>
            <textarea
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Add reminders, concerns, or context for this candidate..."
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition"
            >
              {loading ? "Importing..." : "Import and assess"}
            </button>
            <Link
              href={`/projects/${projectId}`}
              className="px-6 py-2 text-gray-600 hover:text-gray-900 transition"
            >
              Cancel
            </Link>
          </div>
        </form>

        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">What helps the analysis most</h3>
          <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
            <li>The quoted rent, deposit, management fee, and any extra charges.</li>
            <li>Lease term, move-in timing, and repair responsibility details.</li>
            <li>Any notes that explain what makes this candidate attractive or risky.</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
