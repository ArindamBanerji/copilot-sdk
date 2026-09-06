/** Share only overlapping reads. Completed values are never retained. */
const pendingReads = new Map<string, Promise<unknown>>();

export function coalesceRead<T>(key: string, load: () => Promise<T>): Promise<T> {
  const existing = pendingReads.get(key);
  if (existing) return existing as Promise<T>;
  const pending = Promise.resolve().then(load);
  pendingReads.set(key, pending);
  const remove = () => {
    if (pendingReads.get(key) === pending) pendingReads.delete(key);
  };
  void pending.then(remove, remove);
  return pending;
}

/** A read after a mutation must not join work started before that mutation. */
export async function withReadInvalidation<T>(write: () => Promise<T>): Promise<T> {
  pendingReads.clear();
  try {
    return await write();
  } finally {
    pendingReads.clear();
  }
}
