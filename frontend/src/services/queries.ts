import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';
import { useStore } from '../store';
import { SimulationRequest } from '../types';

export function useDashboardStats() {
  const refreshIntervalMs = useStore((state) => state.refreshIntervalMs);
  return useQuery({
    queryKey: ['dashboardStats'],
    queryFn: () => api.fetchDashboardStats(),
    refetchInterval: refreshIntervalMs,
  });
}

export function useThreads() {
  const refreshIntervalMs = useStore((state) => state.refreshIntervalMs);
  return useQuery({
    queryKey: ['threads'],
    queryFn: () => api.fetchAllThreads(),
    refetchInterval: refreshIntervalMs,
  });
}

export function useAnalytics() {
  const refreshIntervalMs = useStore((state) => state.refreshIntervalMs);
  return useQuery({
    queryKey: ['analytics'],
    queryFn: () => api.fetchAnalytics(),
    refetchInterval: refreshIntervalMs,
  });
}

export function useContactProfile(email: string | null) {
  return useQuery({
    queryKey: ['contactProfile', email],
    queryFn: () => api.fetchContactProfile(email!),
    enabled: !!email,
  });
}

export function useReputation(company: string | null) {
  return useQuery({
    queryKey: ['reputation', company],
    queryFn: () => api.getReputation(company!),
    enabled: !!company,
  });
}

export function useDryRunAgent() {
  return useMutation({
    mutationFn: (emailId: number) => api.dryRunAgent(emailId),
  });
}

export function useSendManualReply() {
  const queryClient = useQueryClient();
  const setActionMessage = useStore.getState().setActionMessage;
  
  return useMutation({
    mutationFn: ({ emailId, body, sender }: { emailId: number; body: string; sender: string }) =>
      api.sendManualReply(emailId, body, sender),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['threads'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setActionMessage(`Reply sent successfully for message #${variables.emailId}.`);
    },
    onError: () => {
      setActionMessage('Failed to send reply.');
    },
  });
}

export function useUpdateDraft() {
  const queryClient = useQueryClient();
  const setActionMessage = useStore.getState().setActionMessage;

  return useMutation({
    mutationFn: ({ draftId, proposedContent }: { draftId: number; proposedContent: string }) =>
      api.updateDraft(draftId, proposedContent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threads'] });
      setActionMessage('Draft updated successfully.');
    },
    onError: () => {
      setActionMessage('Failed to update draft.');
    },
  });
}

export function useApproveDraft() {
  const queryClient = useQueryClient();
  const setActionMessage = useStore.getState().setActionMessage;

  return useMutation({
    mutationFn: ({ draftId, approvedBy }: { draftId: number; approvedBy: string }) =>
      api.approveDraft(draftId, approvedBy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threads'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setActionMessage('Draft approved and sent.');
    },
    onError: (err: any) => {
      setActionMessage(`Draft approval failed: ${err.message || 'conflict or database error'}`);
    },
  });
}

export function useUpdateContactStatus() {
  const queryClient = useQueryClient();
  const setActionMessage = useStore.getState().setActionMessage;

  return useMutation({
    mutationFn: ({ email, updates }: { email: string; updates: any }) =>
      api.updateContactStatus(email, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['contactProfile', variables.email] });
      queryClient.invalidateQueries({ queryKey: ['threads'] });
      setActionMessage(`Contact status for ${variables.email} updated.`);
    },
    onError: () => {
      setActionMessage('Failed to update contact status.');
    },
  });
}

export function useSimulateStream() {
  const queryClient = useQueryClient();
  const setActionMessage = useStore.getState().setActionMessage;

  return useMutation({
    mutationFn: (request: SimulationRequest) => api.simulateStream(request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['threads'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      if (data) {
        setActionMessage(
          `Simulation complete. Processed ${data.processed} emails, ${data.succeeded} succeeded.`
        );
      } else {
        setActionMessage('Simulation finished with errors.');
      }
    },
    onError: (err: any) => {
      setActionMessage(`Simulation failed: ${err.message || 'unknown error'}`);
    },
  });
}
