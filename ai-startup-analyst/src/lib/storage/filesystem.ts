import { Project, ProjectSummary } from '@/core/types/project';
import { ProjectStore } from './interface';
import fs from 'fs/promises';
import path from 'path';

export class FilesystemProjectStore implements ProjectStore {
  private baseDir: string;

  constructor(baseDir: string) {
    this.baseDir = baseDir;
  }

  async save(project: Project): Promise<void> {
    const dir = path.join(this.baseDir, project.id);
    await fs.mkdir(dir, { recursive: true });

    // Atomic write: write to temp, then rename
    const tmpPath = path.join(dir, 'project.json.tmp');
    const finalPath = path.join(dir, 'project.json');
    await fs.writeFile(tmpPath, JSON.stringify(project, null, 2));
    await fs.rename(tmpPath, finalPath);
  }

  async load(id: string): Promise<Project | null> {
    try {
      const filePath = path.join(this.baseDir, id, 'project.json');
      const data = await fs.readFile(filePath, 'utf-8');
      return JSON.parse(data);
    } catch {
      return null;
    }
  }

  async list(): Promise<ProjectSummary[]> {
    try {
      const entries = await fs.readdir(this.baseDir);
      const summaries: ProjectSummary[] = [];

      for (const entry of entries) {
        const project = await this.load(entry);
        if (project) {
          summaries.push({
            id: project.id,
            idea: project.idea,
            createdAt: project.createdAt,
            updatedAt: project.updatedAt,
            sectionCount: Object.keys(project.sections).length,
            totalTokens: project.metadata.totalTokensUsed,
          });
        }
      }

      return summaries;
    } catch {
      return [];
    }
  }

  async delete(id: string): Promise<void> {
    const dir = path.join(this.baseDir, id);
    await fs.rm(dir, { recursive: true, force: true });
  }
}
