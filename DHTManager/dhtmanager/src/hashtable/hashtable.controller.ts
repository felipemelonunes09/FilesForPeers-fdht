import { Controller, Get, Post, Body, Patch, Param, Delete } from '@nestjs/common';
import { HashtableService } from './hashtable.service';

@Controller('hashtable')
export class HashtableController {
  constructor(private readonly hashtableService: HashtableService) {}

  @Post()
  create(@Body() createHashtableDto: any) {
    return this.hashtableService.create(createHashtableDto);
  }

  @Get()
  findAll() {
    return this.hashtableService.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.hashtableService.findOne(+id);
  }

  @Patch(':id')
  update(@Param('id') id: string, @Body() updateHashtableDto: any) {
    return this.hashtableService.update(+id, updateHashtableDto);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    return this.hashtableService.remove(+id);
  }
}
