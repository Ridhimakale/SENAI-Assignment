import { create } from 'zustand';

export type ViewType = 'inbox' | 'thread' | 'analytics' | 'simulator';
export type InboxTabType = 'All' | 'Needs Human' | 'Auto-Replied' | 'Escalated' | 'Spam';
export type SortByType = 'priority' | 'lastActivity' | 'sentiment';
export type ConnectionStateType = 'live' | 'demo' | 'loading';

interface AppState {
  activeView: ViewType;
  selectedId: string | null;
  inboxTab: InboxTabType;
  searchQuery: string;
  sortBy: SortByType;
  connectionState: ConnectionStateType;
  actionMessage: string;
  draftBodies: Record<string, string>;
  assignees: Record<string, string>;
  refreshIntervalMs: number;
  
  setActiveView: (view: ViewType) => void;
  setSelectedId: (id: string | null) => void;
  setInboxTab: (tab: InboxTabType) => void;
  setSearchQuery: (query: string) => void;
  setSortBy: (sortBy: SortByType) => void;
  setConnectionState: (state: ConnectionStateType) => void;
  setActionMessage: (msg: string) => void;
  updateDraftBody: (threadId: string, body: string) => void;
  updateAssignee: (threadId: string, assignee: string) => void;
  setRefreshIntervalMs: (ms: number) => void;
}

export const useStore = create<AppState>((set) => ({
  activeView: 'inbox',
  selectedId: null,
  inboxTab: 'All',
  searchQuery: '',
  sortBy: 'priority',
  connectionState: 'loading',
  actionMessage: 'Dashboard ready.',
  draftBodies: {},
  assignees: {},
  refreshIntervalMs: 10000,

  setActiveView: (activeView) => set({ activeView }),
  setSelectedId: (selectedId) => set({ selectedId }),
  setInboxTab: (inboxTab) => set({ inboxTab }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  setSortBy: (sortBy) => set({ sortBy }),
  setConnectionState: (connectionState) => set({ connectionState }),
  setActionMessage: (actionMessage) => set({ actionMessage }),
  updateDraftBody: (threadId, body) =>
    set((state) => ({
      draftBodies: { ...state.draftBodies, [threadId]: body },
    })),
  updateAssignee: (threadId, assignee) =>
    set((state) => ({
      assignees: { ...state.assignees, [threadId]: assignee },
    })),
  setRefreshIntervalMs: (refreshIntervalMs) => set({ refreshIntervalMs }),
}));
