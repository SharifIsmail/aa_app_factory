import { DEFAULT_FONT_FAMILY } from './types';

export const commonChartOptions = {
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        font: {
          family: DEFAULT_FONT_FAMILY,
          size: 12,
        },
        boxWidth: 12,
        padding: 25,
        usePointStyle: true,
      },
    },
    tooltip: {
      titleFont: {
        family: DEFAULT_FONT_FAMILY,
      },
      bodyFont: {
        family: DEFAULT_FONT_FAMILY,
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      titleColor: '#374151',
      bodyColor: '#374151',
      borderColor: '#E5E7EB',
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: true,
    },
  },
  scales: {
    x: {
      ticks: {
        font: {
          family: DEFAULT_FONT_FAMILY,
          size: 11,
        },
        color: '#374151',
      },
      display: true,
      title: {
        display: true,
        text: 'X-axis',
        font: {
          size: 12,
          weight: 'bold' as const,
        },
        color: '#374151',
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.1)',
      },
    },
    y: {
      type: 'linear' as const,
      display: true,
      position: 'left' as const,
      title: {
        display: true,
        text: 'Y-axis',
        font: {
          family: DEFAULT_FONT_FAMILY,
          size: 12,
          weight: 'bold' as const,
        },
        color: '#374151',
      },
      ticks: {
        color: '#374151',
        font: {
          family: DEFAULT_FONT_FAMILY,
          size: 11,
        },
      },
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.1)',
      },
    },
  },
};
