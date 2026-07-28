import { Project, ProjectSummary } from '@/core/types/project';

export interface ProjectStore {
  save(project: Project): Promise<void>;
  load(id: string): Promise<Project | null>;
  list(): Promise<ProjectSummary[]>;
  delete(id: string): Promise<void>;
}
