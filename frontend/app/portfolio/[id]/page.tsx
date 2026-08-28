import { WizardClient } from "./WizardClient";

// Next 15: route params arrive as a Promise. Thin server wrapper; all interactivity (autosave,
// live score, finalise) lives in the client orchestrator.
export default async function AssessmentWizardPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <WizardClient id={id} />;
}
