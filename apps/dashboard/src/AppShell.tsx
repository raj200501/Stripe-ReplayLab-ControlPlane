import { Route, Routes } from 'react-router-dom'
import { CommandPalette } from './components/CommandPalette'
import { Layout } from './components/Layout'
import {
  DiffViewerPage,
  FindingsPage,
  LiveReplayPage,
  MerchantSandboxPage,
  OverviewPage,
  RunDetailPage,
  RunExplorerPage,
  ScenarioBuilderPage,
  ScenarioLibraryPage,
  SettingsPage
} from './pages'

export function AppShell() {
  return (
    <Layout>
      <CommandPalette />
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/scenario-library" element={<ScenarioLibraryPage />} />
        <Route path="/scenario-builder" element={<ScenarioBuilderPage />} />
        <Route path="/run-explorer" element={<RunExplorerPage />} />
        <Route path="/run-detail" element={<RunDetailPage />} />
        <Route path="/live-replay" element={<LiveReplayPage />} />
        <Route path="/findings" element={<FindingsPage />} />
        <Route path="/diff-viewer" element={<DiffViewerPage />} />
        <Route path="/merchant-sandbox" element={<MerchantSandboxPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Layout>
  )
}
