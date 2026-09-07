export interface DataExport {
  schema_version: string;
  exported_at: string;
  user_id: string;
  data: Record<string, Record<string, unknown>[]>;
  exclusions: string[];
}
export interface DataSummary { is_guest: boolean; counts: Record<string, number>; retention: string }
export interface DeletionResult { deleted: boolean; scope: 'account' | 'guest' | 'session'; counts: Record<string, number>; message: string }