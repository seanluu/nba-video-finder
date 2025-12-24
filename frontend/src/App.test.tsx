import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders NBA Video Finder', () => {
  render(<App />);
  const titleElement = screen.getByText(/NBA Clip Finder/i);
  expect(titleElement).toBeInTheDocument();
});
