import { Col, Panel, Row } from "@canonical/react-components";
import { CategoryList } from "../components";

export default function Dashboard() {

    return (
        <>
            <Panel title="Dashboard">
                <div className={"u-fixed-width"}>
                    <h4 className="">Top snaps per category</h4>
                    <Row>
                        <Col size={4}>
                            <CategoryList category="popular" label="Most popular" />
                        </Col>

                        <Col size={4}>
                            <CategoryList category="recent" label="Recently updated" />
                        </Col>

                        <Col size={4}>
                            <CategoryList category="trending" label="Trending" />
                        </Col>
                    </Row>
                </div>
            </Panel>
        </>
    )
}