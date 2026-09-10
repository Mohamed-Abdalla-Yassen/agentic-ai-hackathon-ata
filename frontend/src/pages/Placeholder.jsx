import { EmptyState } from '../components/ui/primitives'

/**
 * Temporary stand-in so every route in the nav resolves while the app is
 * built up in parts. Part 2 replaces the owner route, part 3 the booker
 * routes; this file goes away once both are in.
 */
export default function Placeholder({ title, description, icon }) {
  return (
    <div className="container fade-in">
      <EmptyState icon={icon} title={title} description={description} />
    </div>
  )
}
