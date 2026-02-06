import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type {
    ApiEventResponse,
    ApiStatsResponse,
    Source,
    RawEvent,
    EventFilters
} from '../types/database';

// ====================================================================
// EVENTS ENDPOINTS
// ====================================================================

export const useEvents = (filters: EventFilters = {}) => {
    return useQuery({
        queryKey: ['events', filters],
        queryFn: async () => {
            const params = new URLSearchParams();

            if (filters.type) params.append('type', filters.type);
            if (filters.zone) params.append('zone', filters.zone);
            if (filters.status) params.append('status', filters.status);
            if (filters.limit) params.append('limit', filters.limit.toString());
            if (filters.offset) params.append('offset', filters.offset.toString());

            const { data } = await apiClient.get<ApiEventResponse[]>(`/api/events?${params}`);
            return data;
        },
    });
};

export const useEventDetail = (eventId: string) => {
    return useQuery({
        queryKey: ['event', eventId],
        queryFn: async () => {
            const { data } = await apiClient.get<ApiEventResponse>(`/api/events/${eventId}`);
            return data;
        },
        enabled: !!eventId,
    });
};

// ====================================================================
// RAW EVENTS ENDPOINTS
// ====================================================================

export const useRawEvents = (limit: number = 10, offset: number = 0) => {
    return useQuery({
        queryKey: ['raw-events', limit, offset],
        queryFn: async () => {
            const { data } = await apiClient.get<RawEvent[]>(`/api/raw-events?limit=${limit}&offset=${offset}`);
            return data;
        },
    });
};

// ====================================================================
// SOURCES ENDPOINTS
// ====================================================================

export const useSources = (activeOnly: boolean = true) => {
    return useQuery({
        queryKey: ['sources', activeOnly],
        queryFn: async () => {
            const { data } = await apiClient.get<Source[]>(`/api/sources?active_only=${activeOnly}`);
            return data;
        },
    });
};

// ====================================================================
// STATISTICS ENDPOINTS
// ====================================================================

export const useStats = () => {
    return useQuery({
        queryKey: ['stats'],
        queryFn: async () => {
            const { data } = await apiClient.get<ApiStatsResponse>('/api/stats');
            return data;
        },
        refetchInterval: 30000, // Actualizar cada 30 segundos
    });
};

// ==================================================================
// MUTATIONS (for future CRUD operations)
// ====================================================================

export const useUpdateSource = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ sourceId, updates }: { sourceId: string; updates: Partial<Source> }) => {
            const { data } = await apiClient.patch(`/api/sources/${sourceId}`, updates);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sources'] });
        },
    });
};

export const useCreateEvent = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (eventData: any) => {
            const { data } = await apiClient.post('/api/events', eventData);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['events'] });
            queryClient.invalidateQueries({ queryKey: ['stats'] });
        },
    });
};

export const useUpdateEventStatus = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ eventId, status }: { eventId: string; status: string }) => {
            const { data } = await apiClient.patch(`/api/events/${eventId}`, { status });
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['events'] });
            queryClient.invalidateQueries({ queryKey: ['stats'] });
        },
    });
};

// Provinces
export const useProvinces = () => {
    return useQuery({
        queryKey: ['provinces'],
        queryFn: async () => {
            const response = await apiClient.get('/api/provinces');
            return response.data;
        },
        staleTime: Infinity, // Provinces don't change
    });
};
