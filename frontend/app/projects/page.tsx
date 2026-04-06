"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { createProject, deleteProject, getCurrentUser, getProjects } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { Project } from "@/lib/types";

function formatProjectStatus(status: Project["status"]) {
  switch (status) {
    case "active":
      return "Active";
    case "archived":
      return "Archived";
    case "completed":
      return "Completed";
    default:
      return status;
  }
}

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showDelete, setShowDelete] = useState<Project | null>(null);
  const [title, setTitle] = useState("");
  const [maxBudget, setMaxBudget] = useState("");
  const [user, setUser] = useState<{ email: string } | null>(null);
  const [formError, setFormError] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [deletingProjectId, setDeletingProjectId] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    void loadData(token);
  }, [router]);

  const loadData = async (token: string) => {
    try {
      const [userData, projectsData] = await Promise.all([getCurrentUser(token), getProjects(token)]);
      setUser(userData);
      setProjects(projectsData.projects);
    } catch (err) {
      console.error("Failed to load data:", err);
      clearToken();
      router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();
    if (!token) return;

    try {
      setFormError("");
      const newProject = await createProject(token, {
        title,
        max_budget: maxBudget ? parseInt(maxBudget, 10) : undefined,
      });
      setProjects((current) => [newProject, ...current]);
      setShowCreate(false);
      setTitle("");
      setMaxBudget("");
    } catch (err) {
      console.error("Failed to create project:", err);
      setFormError(err instanceof Error ? err.message : "Failed to create project.");
    }
  };

  const handleDelete = async () => {
    const token = getToken();
    if (!token || !showDelete) return;

    setDeletingProjectId(showDelete.id);
    setDeleteError("");
    try {
      await deleteProject(token, showDelete.id);
      setProjects((current) => current.filter((project) => project.id !== showDelete.id));
      setShowDelete(null);
    } catch (err) {
      console.error("Failed to delete project:", err);
      setDeleteError(err instanceof Error ? err.message : "Failed to delete project.");
    } finally {
      setDeletingProjectId(null);
    }
  };

  const handleLogout = () => {
    clearToken();
    router.push("/");
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading projects...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-primary-600 mb-2">Workspace</p>
            <h1 className="text-2xl font-bold text-gray-900">Search projects</h1>
            {user && <p className="text-sm text-gray-600 mt-1">{user.email}</p>}
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowCreate(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
            >
              New project
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 transition"
            >
              Sign out
            </button>
          </div>
        </div>

        {showCreate && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-xl font-bold mb-4">Create project</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Project title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Spring 2026 search"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Budget cap in HKD (optional)</label>
                  <input
                    type="number"
                    value={maxBudget}
                    onChange={(e) => setMaxBudget(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="22000"
                  />
                </div>
                {formError && <p className="text-sm text-red-600">{formError}</p>}
                <div className="flex gap-3 justify-end">
                  <button
                    type="button"
                    onClick={() => setShowCreate(false)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-900"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Create
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {showDelete && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-xl font-bold mb-4">Delete project</h2>
              <p className="text-gray-600 mb-4">
                Delete <span className="font-medium text-gray-900">{showDelete.title}</span> and all of its
                candidates, assessments, and investigation items?
              </p>
              <p className="text-sm text-red-600 mb-6">This action cannot be undone.</p>
              {deleteError && <p className="text-sm text-red-600 mb-4">{deleteError}</p>}
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setShowDelete(null)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-900"
                  disabled={deletingProjectId === showDelete.id}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => void handleDelete()}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                  disabled={deletingProjectId === showDelete.id}
                >
                  {deletingProjectId === showDelete.id ? "Deleting..." : "Delete project"}
                </button>
              </div>
            </div>
          </div>
        )}

        {projects.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
            </div>
            <h2 className="text-xl font-medium text-gray-700 mb-2">No projects yet</h2>
            <p className="text-gray-500 mb-4">
              Create your first search workspace and start organizing rental candidates.
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Create project
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <div
                key={project.id}
                className="p-6 bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition"
              >
                <div className="flex items-start justify-between gap-3">
                  <Link href={`/projects/${project.id}`} className="block flex-1 min-w-0">
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">{project.title}</h3>
                    {project.max_budget && (
                      <p className="text-sm text-gray-600">Budget cap: HKD {project.max_budget.toLocaleString()}</p>
                    )}
                    <p className="text-sm text-gray-500 mt-2">Status: {formatProjectStatus(project.status)}</p>
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      setDeleteError("");
                      setShowDelete(project);
                    }}
                    className="text-sm text-red-600 hover:text-red-700"
                    aria-label={`Delete ${project.title}`}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
