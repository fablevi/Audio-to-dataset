import { Provider } from "@react-spectrum/s2";
import { createContext, useContext, useState, useMemo, useCallback, useEffect, type ReactNode } from 'react';

interface ThemeContextType {
  colorScheme: 'light' | 'dark';
  setColorScheme: (scheme: 'light' | 'dark') => void;
  toggleTheme: () => void;
  getTheme: () => 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [colorScheme, setColorSchemeState] = useState<'light' | 'dark'>('light');

  const setColorScheme = useCallback((newScheme: 'light' | 'dark') => {
    setColorSchemeState(newScheme);
  }, []);

  const toggleTheme = useCallback(() => {
    setColorScheme(colorScheme === 'light' ? 'dark' : 'light');
  }, [colorScheme, setColorScheme]);

  const getTheme = () => colorScheme;

  const mediaQuery = useMemo(() => {
    return window.matchMedia('(prefers-color-scheme: dark)');
  }, []);

  const handleMediaChange = useCallback(() => {
    setColorScheme(mediaQuery.matches ? 'dark' : 'light');
  }, [mediaQuery, setColorScheme]);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const initialTheme = mediaQuery.matches ? 'dark' : 'light';
    setColorSchemeState(initialTheme);

    mediaQuery.addEventListener('change', handleMediaChange);

    return () => {
      mediaQuery.removeEventListener('change', handleMediaChange);
    };
  }, [handleMediaChange]);

  // ✅ Add this to set CSS variables based on theme
  useEffect(() => {
    const root = document.documentElement;
    if (colorScheme === 'dark') {
      root.style.setProperty('--background', '#121212');
      root.style.setProperty('--foreground', '#ffffff');
      root.style.setProperty('--primary', '#0070f3');
      root.style.setProperty('--border', '#333333');
    } else {
      root.style.setProperty('--background', '#ffffff');
      root.style.setProperty('--foreground', '#000000');
      root.style.setProperty('--primary', '#0070f3');
      root.style.setProperty('--border', '#cccccc');
    }
  }, [colorScheme]);

  return (
    <Provider colorScheme={colorScheme} locale="en-US">
      <ThemeContext.Provider value={{ colorScheme, setColorScheme, toggleTheme, getTheme }}>
        {children}
      </ThemeContext.Provider>
    </Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};