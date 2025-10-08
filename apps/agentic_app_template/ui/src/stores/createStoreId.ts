/*
 * Store Namespace Configuration
 * -----------------------------
 * This unique namespace ID ensures store identifiers remain distinct across
 * all applications and Assistant instances. It is automatically generated
 * during setup using a cryptographically secure random UUID.
 *
 * Important:
 * - Do not modify this value - changes could cause naming conflicts
 * - Always use the createStoreId function below when creating store IDs
 * - This system ensures safe coexistence of multiple app instances
 */
const APPLICATION_STORES_NAMESPACE: string = '58d997c2-1b69-4f81-8ca2-ce689d7d6401';

export const createStoreId = (
  storeName: string,
  namespace: string = APPLICATION_STORES_NAMESPACE
): string => {
  return `${namespace}-${storeName}`;
};
