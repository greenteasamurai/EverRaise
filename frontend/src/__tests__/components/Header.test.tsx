/// <reference types="vitest/globals" />
/// <reference types="@testing-library/jest-dom" />

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { expect, describe, it } from 'vitest';
import Header from '../../components/Header';

// Create a wrapper to provide necessary context for the component
const HeaderWrapper = () => (
  <BrowserRouter>
    <Header />
  </BrowserRouter>
);

describe('Header Component', () => {
  it('renders without crashing', () => {
    render(<HeaderWrapper />);
    // Check if the header is rendered
    const headerElement = screen.getByRole('banner');
    expect(headerElement).toBeInTheDocument();
  });

  it('displays the app name', () => {
    render(<HeaderWrapper />);
    // Check if the app name is displayed
    const appNameElement = screen.getByText(/EverRaise/i);
    expect(appNameElement).toBeInTheDocument();
  });
}); 