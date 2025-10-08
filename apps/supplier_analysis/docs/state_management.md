# State Management in LKSG Risks Project

## TLDR
- **Frontend**: Uses Vue.js reactivity with localStorage for session continuity. Polls backend every second for real-time updates.
- **Backend**: Maintains complete state in memory (WorkLogManager) during active sessions. Only persists to disk on completion.
- **State Flow**: 
  - User action → UUID generation → In-memory state creation
  - Frontend polls every second for full state updates
  - State lives in memory until completion
  - Final state persisted to disk
- **Key Features**:
  - Real-time updates via polling
  - No database queries for active state
  - Session persistence across page reloads
  - Fail-fast error handling
  - No silent failures or fallbacks

## Overview
This document provides a comprehensive overview of the state management approaches used in the LKSG Risks Project. The system employs a multi-layered state management strategy across frontend and backend components, with a strong emphasis on reliability, persistence, and real-time updates.

## Frontend State Management

### Component-Level State
The frontend primarily uses Vue.js's built-in reactivity system with a focus on component-level state management:

#### State Structure
1. **Local Component State**
   - Uses Vue's `ref` and `reactive` for local state
   - Example from `LkSGHomepage.vue`:
     ```typescript
     const searchId = ref<string | null>(null)
     const isRisks = ref(false)
     const showSearchInput = ref(true)
     const showConfigurePopup = ref(false)
     const showHowThisWorksPopup = ref(false)
     ```

2. **Props and Events**
   - Parent-child communication through props
   - Event-based state updates
   - Example:
     ```typescript
     <InputCompanySearch 
       @search-started="handleSearchStarted" 
       @risks-search-started="handleSearchStarted" 
     />
     ```

3. **Local Storage Integration**
   - Persistent state management through `localStorage`
   - Implemented in `storage.ts`:
     ```typescript
     export const storageUtils = {
       saveSearchId(searchId: string): void {
         localStorage.setItem(STORAGE_KEYS.SEARCH_ID, searchId)
       },
       getSearchId(): string | null {
         return localStorage.getItem(STORAGE_KEYS.SEARCH_ID)
       },
       clearSearchId(): void {
         localStorage.removeItem(STORAGE_KEYS.SEARCH_ID)
       }
     }
     ```

#### Real-time State Updates
1. **Polling Mechanism**
   - Frontend polls backend every second for state updates
   - Uses the stored UUID to fetch current state
   - Full state refresh on each poll
   - Example polling implementation:
     ```typescript
     // In WorkCompanySearch.vue
     const pollInterval = ref<NodeJS.Timeout>()
     
     const startPolling = () => {
       pollInterval.value = setInterval(async () => {
         try {
           const response = await fetch(`/company-data-search-status/${props.searchId}`)
           const data = await response.json()
           // Update component state with full response
           currentState.value = data
         } catch (error) {
           console.error('Polling error:', error)
           stopPolling()
         }
       }, 1000)
     }
     
     const stopPolling = () => {
       if (pollInterval.value) {
         clearInterval(pollInterval.value)
       }
     }
     ```

2. **State Synchronization**
   - Local storage maintains session continuity
   - UUID persistence across page reloads
   - Automatic state recovery on page load
   - Example:
     ```typescript
     onMounted(() => {
       const savedSearchId = storageUtils.getSearchId()
       if (savedSearchId) {
         searchId.value = savedSearchId
         showSearchInput.value = false
         startPolling() // Resume polling for existing session
       }
     })
     ```

## Backend State Management

### In-Memory State Management

#### WorkLogManager
A singleton class for managing active work logs and execution states in memory:

```python
class WorkLogManager:
    def __init__(self):
        # In-memory dictionary for active work logs
        self._work_logs: Dict[str, WorkLog] = {}
    
    def get(self, execution_id: str) -> Optional[WorkLog]:
        return self._work_logs.get(execution_id)
    
    def set(self, execution_id: str, work_log: WorkLog) -> None:
        self._work_logs[execution_id] = work_log
    
    def contains(self, execution_id: str) -> bool:
        return execution_id in self._work_logs
    
    def update_status(self, execution_id: str, status: TaskStatus) -> bool:
        if execution_id in self._work_logs:
            self._work_logs[execution_id].status = status
            return True
        return False
```

#### In-Memory State Structure
1. **Active Sessions**
   - Each session identified by UUID
   - Complete state stored in memory
   - Real-time updates to state
   - No persistence until completion

2. **State Components**
   - Task status and progress
   - Tool execution logs
   - Extracted data
   - Error states and messages

3. **State Access**
   - Direct memory access for active sessions
   - No database queries for active state
   - Immediate state updates
   - Example:
     ```python
     @router.get("/company-data-search-status/{uuid}")
     async def company_data_search_status(
         uuid: str, 
         work_log_manager: WorkLogManager = Depends(get_work_log_manager)
     ) -> Json:
         if not work_log_manager.contains(uuid):
             raise HTTPException(status_code=404, detail=f"Search job with ID {uuid} not found")
         
         # Direct memory access to work log
         work_log = work_log_manager.get(uuid)
         return {
             "status": work_log.status.value,
             "uuid": uuid,
             "tasks": work_log.tasks,
             "tool_logs": work_log.tool_logs,
             "extracted_data": work_log.extracted_data
         }
     ```

### State Lifecycle

1. **Session Creation**
   ```python
   execution_id = str(uuid.uuid4())
   work_log = create_company_data_work_log(research_type=research_type, work_log_id=execution_id)
   work_log.status = TaskStatus.IN_PROGRESS
   work_log_manager.set(execution_id, work_log)
   ```

2. **State Updates**
   ```python
   # In-memory state update
   work_log.tasks.append(new_task)
   work_log.tool_logs.extend(new_logs)
   work_log.extracted_data.update(new_data)
   ```

3. **Session Completion**
   ```python
   work_log.status = TaskStatus.COMPLETED
   # Persist final state to disk
   persistence_service.save_to_cache(execution_id, work_log)
   ```

### Persistent State Management

#### PersistenceService
A singleton service responsible for persistent state operations:

##### Directory Structure
```python
def __init__(self):
    self.temp_dir = tempfile.gettempdir()
    self.cache_dir = os.path.join(self.temp_dir, 'lksg_cache')
    self.artifacts_dir = os.path.join(self.temp_dir, 'lksg_artifacts_data')
    self.company_data_dir = self._ensure_company_data_dir()
```

##### Cache Operations
```python
def load_from_cache(self, cache_id: str) -> Optional[Any]:
    filename = self._generate_cache_filename(cache_id)
    cache_path = os.path.join(self.cache_dir, filename)
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return None

def save_to_cache(self, cache_id: str, data: Any) -> str:
    filename = self._generate_cache_filename(cache_id)
    cache_path = os.path.join(self.cache_dir, filename)
    with open(cache_path, 'w') as f:
        json.dump(data, f)
    return cache_path
```

## State Flow

### Frontend to Backend
1. **User Action**
   - Component method triggered
   - State updated locally
   - API call initiated

2. **Backend Processing**
   - Request received
   - Execution ID generated
   - Work log created in memory
   - Background task started

3. **Real-time Updates**
   - Frontend polls every second
   - Backend serves in-memory state
   - Full state refresh on each poll
   - State persisted only on completion

### Backend Processing Flow
1. **Initialization**
   ```python
   execution_id = str(uuid.uuid4())
   work_log = create_company_data_work_log(research_type=research_type, work_log_id=execution_id)
   work_log.status = TaskStatus.IN_PROGRESS
   work_log_manager.set(execution_id, work_log)
   ```

2. **Task Execution**
   ```python
   background_tasks.add_task(extract_company_data, data["company_name"], execution_id, work_log, research_type)
   ```

3. **Status Updates**
   ```python
   work_log = work_log_manager.get(uuid)
   return {
       "status": work_log.status.value,
       "uuid": uuid,
       "tasks": work_log.tasks,
       "tool_logs": work_log.tool_logs,
       "extracted_data": work_log.extracted_data
   }
   ```

## Error Handling

### Frontend
- Explicit error handling in component methods
- No silent failures or fallbacks
- Clear error propagation to UI
- Local storage error handling
- Polling error recovery

### Backend
- Structured error handling in routes
- Explicit status updates in WorkLogManager
- Detailed error logging with stack traces
- No silent failures in persistence operations
- HTTP exception handling:
  ```python
  if not work_log_manager.contains(uuid):
      raise HTTPException(status_code=404, detail=f"Search job with ID {uuid} not found")
  ```

## Best Practices

1. **State Updates**
   - Always use explicit state updates
   - Avoid implicit state changes
   - Document state transitions
   - Clear state ownership
   - Regular polling for real-time updates

2. **Error Handling**
   - Never swallow errors
   - Log full stack traces
   - Fail fast on errors
   - No fallback mechanisms
   - Explicit error boundaries
   - Polling error recovery

3. **Persistence**
   - Use atomic operations
   - Implement proper error handling
   - Maintain data integrity
   - Clear documentation of storage locations
   - Regular cache cleanup
   - In-memory state management

4. **Concurrency**
   - Thread-safe operations
   - Proper locking mechanisms
   - Clear state ownership
   - Background task management
   - Polling rate control

## Security Considerations

1. **Data Storage**
   - Secure file permissions
   - Proper access controls
   - Data encryption where needed
   - Secure temporary storage
   - In-memory data protection

2. **State Access**
   - Proper authentication
   - Authorization checks
   - Input validation
   - Rate limiting
   - Session validation

3. **Error Handling**
   - Secure error messages
   - No sensitive data in logs
   - Proper error boundaries
   - Audit logging
   - Polling security 

## Future Improvements

### Client-Side State Management with Pinia

#### Planned Architecture
- **Pinia Store Implementation**
  - Centralized state management on the client
  - Dedicated stores for different data types:
    - Company data store
    - Risk analysis store
    - Search progress store
  - Type-safe state management
  - DevTools integration for debugging

#### Benefits
1. **Reduced Bandwidth Usage**
   - Only fetch new/updated data from server
   - Store complete state locally
   - Minimize payload size in polling requests
   - Example:
     ```typescript
     // Current approach - fetching full state
     const response = await fetch(`/company-data-search-status/${props.searchId}`)
     const data = await response.json()
     currentState.value = data

     // Future approach - only fetch updates
     const response = await fetch(`/company-data-search-status/${props.searchId}?since=${lastUpdate}`)
     const updates = await response.json()
     companyStore.applyUpdates(updates)
     ```

2. **Improved Performance**
   - Faster UI updates (no full state refresh)
   - Reduced network traffic
   - Better handling of large datasets
   - Smoother user experience

3. **Better State Management**
   - Centralized state logic
   - Predictable state updates
   - Easier debugging
   - Better TypeScript integration
   - Example store structure:
     ```typescript
     export const useCompanyStore = defineStore('company', {
       state: () => ({
         companies: new Map<string, CompanyData>(),
         lastUpdate: new Date(),
         searchProgress: new Map<string, SearchProgress>()
       }),
       actions: {
         async fetchUpdates(since: Date) {
           const updates = await api.getUpdates(since)
           this.applyUpdates(updates)
         },
         applyUpdates(updates: CompanyUpdates) {
           // Efficiently merge updates with existing state
         }
       }
     })
     ```

4. **Enhanced Developer Experience**
   - Better state organization
   - Easier testing
   - Improved debugging capabilities
   - Better code maintainability

5. **Offline Capabilities**
   - Partial offline support
   - State persistence across sessions
   - Better error recovery
   - Example:
     ```typescript
     // Store state in IndexedDB for offline access
     const offlineStore = {
       saveState(state: CompanyState) {
         indexedDB.save('companyState', state)
       },
       async loadState() {
         return await indexedDB.load('companyState')
       }
     }
     ```

#### Implementation Strategy
1. **Phase 1: Store Setup**
   - Create Pinia stores
   - Define state structure
   - Implement basic actions

2. **Phase 2: State Migration**
   - Move component state to stores
   - Update polling logic
   - Implement update diffing

3. **Phase 3: Optimization**
   - Add offline support
   - Implement caching
   - Add state persistence

4. **Phase 4: Monitoring**
   - Add performance metrics
   - Monitor bandwidth usage
   - Track state update efficiency

This improvement will significantly enhance the application's performance and maintainability while reducing server load and bandwidth usage. 