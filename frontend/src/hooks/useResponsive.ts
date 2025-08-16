import { useState, useEffect } from 'react';

interface Breakpoints {
  sm: boolean;
  md: boolean;
  lg: boolean;
  xl: boolean;
  '2xl': boolean;
}

interface UseResponsiveReturn extends Breakpoints {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  screenWidth: number;
}

export function useResponsive(): UseResponsiveReturn {
  const [screenWidth, setScreenWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024);

  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const breakpoints: Breakpoints = {
    sm: screenWidth >= 640,
    md: screenWidth >= 768,
    lg: screenWidth >= 1024,
    xl: screenWidth >= 1280,
    '2xl': screenWidth >= 1536,
  };

  return {
    ...breakpoints,
    isMobile: screenWidth < 768,
    isTablet: screenWidth >= 768 && screenWidth < 1024,
    isDesktop: screenWidth >= 1024,
    screenWidth,
  };
}

export function useBreakpoint(breakpoint: keyof Breakpoints): boolean {
  const responsive = useResponsive();
  return responsive[breakpoint];
}

export function useMobileFirst() {
  const { isMobile, isTablet, isDesktop } = useResponsive();
  
  return {
    isMobile,
    isTablet, 
    isDesktop,
    // Helper functions for conditional rendering
    showOnMobile: (content: React.ReactNode) => isMobile ? content : null,
    showOnTablet: (content: React.ReactNode) => isTablet ? content : null,
    showOnDesktop: (content: React.ReactNode) => isDesktop ? content : null,
    hideOnMobile: (content: React.ReactNode) => !isMobile ? content : null,
  };
}