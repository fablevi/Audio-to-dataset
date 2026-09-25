import { Col, Container, Row } from "react-bootstrap";
import { LANG } from "./language/locales";

import { Card } from '@react-spectrum/s2/Card';
import { useTheme } from "./helper/ThemeProvider";
import {
  Button,
  CardPreview,
  Image,
  Content,
  Text,
  Footer,
  ActionMenu,
  MenuItem,
  StatusLight,
} from "@react-spectrum/s2";
import { Grid, View } from "@adobe/react-spectrum";

export default function App() {

  const { colorScheme, toggleTheme } = useTheme();


  return (
    <Grid
      areas={[
        'header  header',
        'sidebar content',
        'footer  footer'
      ]}
      columns={['1fr', '3fr']}
      rows={['size-1000', 'auto', 'size-1000']}
      height="size-6000">
      <View gridArea="header" >
 <Card>
        <Button onPress={toggleTheme}>
          click
        </Button>
        <CardPreview>
          <Image src={"preview"} />
        </CardPreview>
        <Content>
          <Text slot="title">Card title</Text>
          <ActionMenu>
            <MenuItem>Edit</MenuItem>
            <MenuItem>Share</MenuItem>
            <MenuItem>Delete</MenuItem>
          </ActionMenu>
          <Text slot="description">Card description. Give a concise overview of the context or functionality that's mentioned in the card title.</Text>
        </Content>
        <Footer>
          <StatusLight size="S" variant="positive">Published</StatusLight>
        </Footer>
      </Card>
      </View>
     
    </Grid>

  )
}