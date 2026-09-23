import {Card, CardPreview, Image, Content, Text, Footer} from '@react-spectrum/s2/Card';
import {ActionMenu, MenuItem} from '@react-spectrum/s2/ActionMenu';
import {StatusLight} from '@react-spectrum/s2/StatusLight';

export default function TestC(){
    return <Card>
  <CardPreview>
    <Image src={""} />
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
} 