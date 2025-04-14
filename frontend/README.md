# EverRaise Frontend

This is the frontend for the EverRaise platform, an AI-driven fundraising solution. The frontend is built with React, TypeScript, and Tailwind CSS.

## Technologies Used

- React 18
- TypeScript
- TanStack Query for data fetching
- React Router for navigation
- Tailwind CSS for styling
- Vite for building and development

## Getting Started

### Prerequisites

- Node.js (v16 or later)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install
# or
yarn install
```

### Development

```bash
# Start the development server
npm run dev
# or
yarn dev
```

This will start the development server at `http://localhost:5173`.

### Building for Production

```bash
# Build the application
npm run build
# or
yarn build
```

This will create a production-ready build in the `dist` directory.

### Running Tests

```bash
# Run tests
npm run test
# or
yarn test
```

## Project Structure

```
frontend/
├── public/            # Public assets
├── src/
│   ├── components/    # Reusable UI components
│   ├── contexts/      # React contexts
│   ├── hooks/         # Custom React hooks
│   ├── layouts/       # Layout components
│   ├── pages/         # Page components
│   ├── services/      # API services
│   ├── styles/        # CSS styles
│   ├── types/         # TypeScript type definitions
│   ├── utils/         # Utility functions
│   ├── App.tsx        # Main App component
│   └── main.tsx       # Entry point
├── .eslintrc.js       # ESLint configuration
├── index.html         # HTML template
├── package.json       # Project dependencies
├── tailwind.config.js # Tailwind CSS configuration
├── tsconfig.json      # TypeScript configuration
└── vite.config.ts     # Vite configuration
```

## Docker

A Dockerfile is provided for containerization. To build and run the Docker container:

```bash
# Build the Docker image
docker build -t everraise-frontend .

# Run the container
docker run -p 80:80 everraise-frontend
```

This will make the application available at `http://localhost`.

## Contributing

Please follow the project's coding standards and commit message conventions when contributing.

## License

This project is proprietary and confidential. 