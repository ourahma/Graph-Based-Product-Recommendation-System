import type { Metadata } from 'next';
import Layout from '@/components/Layout';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'RecSys - Graph-Based Product Recommendations',
  description: 'Advanced recommendation engine powered by Neo4j and Graph Data Science',
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90" fill="%230ea5e9" font-weight="bold">◈</text></svg>',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body>
        <Layout>{children}</Layout>
      </body>
    </html>
  );
}
