import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit';

// Define an initial state and a slice for UI-related state (e.g., theme)
interface UIState {
  theme: 'light' | 'dark' | 'system';
  isSidebarOpen: boolean;
  // Add other UI related states here, e.g., language, notifications settings
}

const initialState: UIState = {
  theme: 'system', // Default theme
  isSidebarOpen: true, // Default sidebar state
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<UIState['theme']>) => {
      state.theme = action.payload;
    },
    toggleSidebar: (state) => {
      state.isSidebarOpen = !state.isSidebarOpen;
    },
    // Add other reducers for UI state here
  },
});

export const { setTheme, toggleSidebar } = uiSlice.actions;

// Configure the Redux store
export const store = configureStore({
  reducer: {
    ui: uiSlice.reducer,
    // Add other slices here as your application grows
    // portfolio: portfolioSlice.reducer, (example for later)
    // marketData: marketDataSlice.reducer, (example for later)
  },
  // Adding middleware like Redux Thunk is done here if needed for async actions
  // middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(loggerMiddleware), // Example
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Optional: Export hooks for typed access to state and dispatch
// import { TypedUseSelectorHook, useDispatch as useReduxDispatch, useSelector as useReduxSelector } from 'react-redux';
// export const useDispatch = () => useReduxDispatch<AppDispatch>();
// export const useSelector: TypedUseSelectorHook<RootState> = useReduxSelector; 