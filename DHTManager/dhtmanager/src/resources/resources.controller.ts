import { Controller, Get, Post, Body, Patch, Param, Delete, UseInterceptors, UploadedFile } from '@nestjs/common';
import { ResourcesService } from './resources.service';
import { FileInterceptor } from '@nestjs/platform-express';
import { Resource } from './entities/resource.entity';

@Controller('resources')
export class ResourcesController {
  constructor(private readonly resourcesService: ResourcesService) {}
  
  @Post('upload')
  @UseInterceptors(FileInterceptor('file'))
  uploadFile(@UploadedFile() file: Express.Multer.File) {
    return {
      message: "File uploaded",
      filePath: file.path
    }
  }

  @Get()
  findAll(): Array<Resource> {
    return this.resourcesService.getFilesLocation();
  }
}
