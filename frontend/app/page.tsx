import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-3xl text-center">
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-primary-600 mb-3">
          Rental Research Workspace
        </p>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">RentWise</h1>
        <p className="text-lg text-gray-600 mb-8">
          A candidate-pool rental assistant that helps you organize listings,
          spot missing information, and decide what to verify next.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/login"
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
          >
            Sign in
          </Link>
          <Link
            href="/projects"
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
          >
            Open workspace
          </Link>
        </div>
      </div>
    </main>
  );
}
