import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { FilesystemProjectStore } from '@/lib/storage/filesystem';
import { Project } from '@/core/types/project';
import fs from 'fs/promises';
import path from 'path';

const TEST_DIR = path.join(process.cwd(), 'test-data');

describe('FilesystemProjectStore', () => {
  let store: FilesystemProjectStore;

  beforeEach(async () => {
    await fs.mkdir(TEST_DIR, { recursive: true });
    store = new FilesystemProjectStore(TEST_DIR);
  });

  afterEach(async () => {
    await fs.rm(TEST_DIR, { recursive: true, force: true });
  });

  const mockProject: Project = {
    id: 'proj_test123',
    idea: 'Test startup idea',
    createdAt: '2026-07-26T10:00:00Z',
    updatedAt: '2026-07-26T10:00:00Z',
    status: 'complete',
    analysis: {
      originalIdea: 'Test startup idea',
      type: 'saas',
      model: 'b2b',
      complexity: 'moderate',
      industry: 'test',
      hasHardware: false,
      hasRegulatoryRequirements: false,
      isTwoSidedMarketplace: false,
      requiresIntegrations: false,
    },
    sections: {},
    chatHistory: [],
    metadata: {
      totalTokensUsed: 1000,
      generationDurationMs: 5000,
      model: 'llama-3.1-70b-versatile',
    },
  };

  it('should save and load a project', async () => {
    await store.save(mockProject);
    const loaded = await store.load('proj_test123');

    expect(loaded).toEqual(mockProject);
  });

  it('should return null for non-existent project', async () => {
    const loaded = await store.load('proj_nonexistent');
    expect(loaded).toBeNull();
  });

  it('should list all projects', async () => {
    await store.save(mockProject);
    await store.save({ ...mockProject, id: 'proj_test456', idea: 'Another idea' });

    const list = await store.list();
    expect(list).toHaveLength(2);
  });

  it('should delete a project', async () => {
    await store.save(mockProject);
    await store.delete('proj_test123');

    const loaded = await store.load('proj_test123');
    expect(loaded).toBeNull();
  });

  it('should handle concurrent saves', async () => {
    const promises = Array.from({ length: 5 }, (_, i) =>
      store.save({ ...mockProject, id: `proj_${i}` })
    );

    await Promise.all(promises);
    const list = await store.list();
    expect(list).toHaveLength(5);
  });
});
