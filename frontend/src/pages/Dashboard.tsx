import { Col, Panel, Row } from "@canonical/react-components";
import { CategoryList } from "../components";

export default function Dashboard() {

	return (
		<Panel title="Dashboard">
			<div className={"u-fixed-width"}>
				<h4 className="">Top snaps per category</h4>
				<Row>
					<Col size={3}>
						<CategoryList category="popular" label="Most popular" />
					</Col>

					<Col size={3}>
						<CategoryList category="recent" label="Recently updated" />
					</Col>

					<Col size={3}>
						<CategoryList category="trending" label="Trending" />
					</Col>
					<Col size={3}>
						<CategoryList category="top_rated" label="Top Rated" />
					</Col>
				</Row>
			</div>
		</Panel>
	)
}
